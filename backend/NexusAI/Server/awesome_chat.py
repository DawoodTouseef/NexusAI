from huggingface_hub import InferenceClient
from ollama_python.endpoints.generate import GenerateAPI
from dotenv import load_dotenv
import base64
import copy
from io import BytesIO
import io
import os
import random
import time
import traceback
import uuid
import requests
import re
import json
import logging
import yaml
from PIL import Image, ImageDraw
from diffusers.utils import load_image
from pydub import AudioSegment
import threading
from Server.get_token_ids import get_token_ids_for_task_parsing, get_token_ids_for_choose_model, count_tokens, get_max_context_length
from huggingface_hub import InferenceApi
from queue import Queue
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
path=os.path.join(BASE_DIR,"Server")

load_dotenv()
config_file=os.path.join(path,"configs","config.yaml")
config = yaml.load(open(config_file, "r"), Loader=yaml.FullLoader)
os.makedirs("logs", exist_ok=True)
os.makedirs("public/images", exist_ok=True)
os.makedirs("public/audios", exist_ok=True)
os.makedirs("public/videos", exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not config["debug"]:
    handler.setLevel(logging.CRITICAL)
logger.addHandler(handler)

log_file = config["log_file"]
if log_file:
    filehandler = logging.FileHandler(log_file)
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)


LLM = config["model"]
inference_mode=config['inference_mode']
model_api=GenerateAPI(model="openchat_3.5")
LLM_encoding = LLM
if config["dev"] and LLM == "mistral-7b-instruct-v0.1":
    LLM_encoding = "mistral-7b-instruct-v0.1"

# check the local_inference_endpoint
Model_Server = None
if inference_mode!="huggingface":
    Model_Server = "http://" + config["local_inference_endpoint"]["host"] + ":" + str(config["local_inference_endpoint"]["port"])
    message = f"The server of local inference endpoints is not running, please start it first. (or using `inference_mode: huggingface` in {config} for a feature-limited experience)"
    try:
        r = requests.get(Model_Server + "/running")
        if r.status_code != 200:
            raise ValueError(message)
    except:
        raise ValueError(message)

task_parsing_highlight_ids = get_token_ids_for_task_parsing(LLM_encoding)
choose_model_highlight_ids = get_token_ids_for_choose_model(LLM_encoding)

MODELS = [json.loads(line) for line in open(os.path.join(path,"data","p0_models.jsonl"), "r").readlines()]
MODELS_MAP = {}
for model in MODELS:
    tag = model["task"]
    if tag not in MODELS_MAP:
        MODELS_MAP[tag] = []
    MODELS_MAP[tag].append(model)
METADATAS = {}
for model in MODELS:
    METADATAS[model["id"]] = model

PROXY = None
if config["proxy"]:
    PROXY = {
        "https": config["proxy"],
    }

HUGGINGFACE_HEADERS = {}
if config["huggingface"]["token"] and config["huggingface"]["token"].startswith("hf_"):  # Check for valid huggingface token in config file
    HUGGINGFACE_HEADERS = {
        "Authorization": f"Bearer {config['huggingface']['token']}",
    }
elif "LLAMA_TOKEN" in os.environ and os.getenv("LLAMA_TOKEN").startswith("hf_"):  # Check for environment variable HUGGINGFACE_ACCESS_TOKEN
    HUGGINGFACE_HEADERS = {
        "Authorization": f"Bearer {os.getenv('LLAMA_TOKEN')}",
    }
else:
    raise ValueError(f"Incorrect HuggingFace token. Please check your {config} file.")

parse_task_demos_or_presteps = open(os.path.join(path,config["demos_or_presteps"]["parse_task"]), "r").read()
choose_model_demos_or_presteps = open(os.path.join(path,config["demos_or_presteps"]["choose_model"]), "r").read()
response_results_demos_or_presteps = open(os.path.join(path,config["demos_or_presteps"]["response_results"]), "r").read()

parse_task_prompt = config["prompt"]["parse_task"]
choose_model_prompt = config["prompt"]["choose_model"]
response_results_prompt = config["prompt"]["response_results"]

parse_task_tprompt = config["tprompt"]["parse_task"]
choose_model_tprompt = config["tprompt"]["choose_model"]
response_results_tprompt = config["tprompt"]["response_results"]



def convert_chat_to_completion(data):
    messages = data.pop('messages', [])
    tprompt = ""
    if messages[0]['role'] == "system":
        tprompt = messages[0]['content']
        messages = messages[1:]
    final_prompt = ""
    for message in messages:
        if message['role'] == "user":
            final_prompt += ("<im_start>"+ "user" + "\n" + message['content'] + "<im_end>\n")
        elif message['role'] == "assistant":
            final_prompt += ("<im_start>"+ "assistant" + "\n" + message['content'] + "<im_end>\n")
        else:
            final_prompt += ("<im_start>"+ "system" + "\n" + message['content'] + "<im_end>\n")
    final_prompt = tprompt + final_prompt
    final_prompt = final_prompt + "<im_start>assistant"
    data["prompt"] = final_prompt
    data['stop'] = data.get('stop', ["<im_end>"])
    data['max_tokens'] = data.get('max_tokens', max(get_max_context_length(LLM) - count_tokens(LLM_encoding, final_prompt), 1))
    return data


def send_request(data):
    data = convert_chat_to_completion(data)
    data=json.dumps(data)
    data_dict=json.loads(data)
    prompt=data_dict['prompt']
    stop=data_dict['stop']
    max_tokens=data_dict['max_tokens']
    client = InferenceClient(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        token=os.getenv("LLAMA_TOKEN"),
    )
    response = ""
    for message in client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stop=stop,
            stream=True,
    ):
        response += message.choices[0].delta.content
    logger.debug(response)
    return response

def replace_slot(text, entries):
    for key, value in entries.items():
        if not isinstance(value, str):
            value = str(value)
        text = text.replace("{{" + key +"}}", value.replace('"', "'").replace('\n', ""))
    return text

def find_json(s):
    s = s.replace("\'", "\"")
    start = s.find("{")
    end = s.rfind("}")
    res = s[start:end+1]
    res = res.replace("\n", "")
    return res

def field_extract(s, field):
    try:
        field_rep = re.compile(f'{field}.*?:.*?"(.*?)"', re.IGNORECASE)
        extracted = field_rep.search(s).group(1).replace("\"", "\'")
    except:
        field_rep = re.compile(f'{field}:\ *"(.*?)"', re.IGNORECASE)
        extracted = field_rep.search(s).group(1).replace("\"", "\'")
    return extracted

def get_id_reason(choose_str):
    reason = field_extract(choose_str, "reason")
    id = field_extract(choose_str, "id")
    choose = {"id": id, "reason": reason}
    return id.strip(), reason.strip(), choose

def record_case(success, **args):
    if success:
        f = open("logs/log_success.jsonl", "a")
    else:
        f = open("logs/log_fail.jsonl", "a")
    log = args
    f.write(json.dumps(log) + "\n")
    f.close()

def image_to_bytes(img_url):
    img_byte = io.BytesIO()
    type = img_url.split(".")[-1]
    load_image(img_url).save(img_byte, format="png")
    img_data = img_byte.getvalue()
    return img_data

def resource_has_dep(command):
    args = command["args"]
    for _, v in args.items():
        if "<GENERATED>" in v:
            return True
    return False

def fix_dep(tasks):
    for task in tasks:
        args = task["args"]
        task["dep"] = []
        for k, v in args.items():
            if "<GENERATED>" in v:
                dep_task_id = int(v.split("-")[1])
                if dep_task_id not in task["dep"]:
                    task["dep"].append(dep_task_id)
        if len(task["dep"]) == 0:
            task["dep"] = [-1]
    return tasks


def unfold(tasks):
    flag_unfold_task = False
    try:
        for task in tasks:
            for key, value in task["args"].items():
                if "<GENERATED>" in value:
                    generated_items = value.split(",")
                    if len(generated_items) > 1:
                        flag_unfold_task = True
                        for item in generated_items:
                            new_task = copy.deepcopy(task)
                            dep_task_id = int(item.split("-")[1])
                            new_task["dep"] = [dep_task_id]
                            new_task["args"][key] = item
                            tasks.append(new_task)
                        tasks.remove(task)
    except Exception as e:
        #print(e)
        traceback.print_exc()
        logger.debug("unfold task failed.")

    if flag_unfold_task:
        logger.debug(f"unfold tasks: {tasks}")

    return tasks


def chitchat(messages):
    data = {
        "messages": messages,
    }
    return send_request(data)

def parse_task(context, input):
    demos_or_presteps = parse_task_demos_or_presteps
    messages = json.loads(demos_or_presteps)
    messages.insert(0, {"role": "system", "content": parse_task_tprompt})

    # cut chat logs
    start = 0
    while start <= len(context):
        history = context[start:]
        prompt = replace_slot(parse_task_prompt, {
            "input": input,
            "context": history
        })
        messages.append({"role": "user", "content": prompt})
        history_text = "<im_end>\nuser<im_start>".join([m["content"] for m in messages])
        num = count_tokens(LLM_encoding, history_text)
        if get_max_context_length(LLM) - num > 800:
            break
        messages.pop()
        start += 2

    logger.debug(messages)
    data = {
        "messages": messages,
        "temperature": 0,
        "logit_bias": {item: config["logit_bias"]["parse_task"] for item in task_parsing_highlight_ids},
    }
    return send_request(data)


def choose_model(input, task, metas):
    prompt = replace_slot(choose_model_prompt, {
        "input": input,
        "task": task,
        "metas": metas,
    })
    demos_or_presteps = replace_slot(choose_model_demos_or_presteps, {
        "input": input,
        "task": task,
        "metas": metas
    })
    messages = json.loads(demos_or_presteps)
    messages.insert(0, {"role": "system", "content": choose_model_tprompt})
    messages.append({"role": "user", "content": prompt})
    logger.debug(messages)
    data = {
        "model": LLM,
        "messages": messages,
        "temperature": 0,
        "logit_bias": {item: config["logit_bias"]["choose_model"] for item in choose_model_highlight_ids}, # 5
    }
    return send_request(data)


def response_results(input,results:dict):
    results = [v for k, v in sorted(results.items(), key=lambda item: item[0])]
    prompt = replace_slot(response_results_prompt, {
        "input": input,
    })
    demos_or_presteps = replace_slot(response_results_demos_or_presteps, {
        "input": input,
        "processes": results
    })
    messages = json.loads(demos_or_presteps)
    messages.insert(0, {"role": "system", "content": response_results_tprompt})
    messages.append({"role": "user", "content": prompt})
    logger.debug(messages)
    data = {
        "model": LLM,
        "messages": messages,
        "temperature": 0,
    }
    return send_request(data)


def collect_result(command,choose, inference_result):
    result = {"task": command}
    result["inference result"] = inference_result
    result["choose model result"] = choose
    logger.debug(f"inference result: {inference_result}")
    return result


def huggingface_model_inference(model_id, data, task,path=None):
    result = {}
    task_url = f"https://api-inference.huggingface.co/models/{model_id}"
    inference = InferenceApi(repo_id=model_id, token=os.getenv("LLAMA_TOKEN"))
    # NLP tasks
    #if task == "question-answering":
    #    task_url = f"https://api-inference.huggingface.co/models/{model_id}"  # InferenceApi does not yet support some tasks
    #    inference = InferenceApi(repo_id=model_id, token=os.getenv("LLAMA_TOKEN"))
    #    inputs = {"question": data["text"], "context": (data["context"] if "context" in data else "")}
    #    result = inference(inputs)
    if task == "sentence-similarity":
        inputs = {"source_sentence": data["text1"], "target_sentence": data["text2"]}
        model_id='sentence-transformers/all-MiniLM-L6-v2'
        task_url = f"https://api-inference.huggingface.co/models/{model_id}"  # InferenceApi does not yet support some tasks
        inference = InferenceApi(repo_id=model_id, token=os.getenv("LLAMA_TOKEN"))
        result = inference(inputs)
    if task in ["text-classification", "token-classification", "text2text-generation", "summarization", #"translation",
                "conversational", "text-generation"]:
        inputs = data["text"]
        model=GenerateAPI(model="llama3")
        result["generated text"]=model.generate(inputs,options={"num_predict":4096}).response

    # CV tasks
    if task == "visual-question-answering" or task == "document-question-answering":
        img_url = data["image"]
        text = data["text"]
        img_data = image_to_bytes(img_url)
        img_base64 = base64.b64encode(img_data)
        name = str(uuid.uuid4())[:4]
        # Write the bytes to a file
        with open(f"public/images/{name}.png", 'wb') as output_file:
            output_file.write(img_data)

        json_data = {}
        json_data["inputs"] = {}
        json_data["inputs"]["question"] = text
        json_data["inputs"]["image"] = img_base64.decode("utf-8")
        model=GenerateAPI("llava")
        result["generated text"]=model.generate(prompt=text,images=[f"public/images/{name}.png"])
        # result = inference(inputs) # not support

    if task == "image-to-image":
         # InferenceApi does not yet support some tasks
        img_url = data["image"]
        img_data = image_to_bytes(img_url)
        # result = inference(data=img_data) # not support
        HUGGINGFACE_HEADERS["Content-Length"] = str(len(img_data))
        r = requests.post(task_url, headers=HUGGINGFACE_HEADERS, data=img_data)
        result = r.json()
        if "path" in result:
            result["generated image"] = result.pop("path")
            path['path']=result.pop('path')
    if task == "text-to-image":
        inputs = data["text"]
        img = inference(inputs)
        name = str(uuid.uuid4())[:4]
        img.save(f"public/images/{name}.png")
        result["generated image"] = f"Path of the Image='/images/{name}.png'"
        path['path']=f'/images/{name}.png'

    if task == "image-segmentation":
        img_url = data["image"]
        img_data = image_to_bytes(img_url)
        image = Image.open(BytesIO(img_data))
        predicted = inference(data=img_data)
        colors = []
        for i in range(len(predicted)):
            colors.append((random.randint(100, 255), random.randint(100, 255), random.randint(100, 255), 155))
        for i, pred in enumerate(predicted):
            label = pred["label"]
            mask = pred.pop("mask").encode("utf-8")
            mask = base64.b64decode(mask)
            mask = Image.open(BytesIO(mask), mode='r')
            mask = mask.convert('L')

            layer = Image.new('RGBA', mask.size, colors[i])
            image.paste(layer, (0, 0), mask)
        name = str(uuid.uuid4())[:4]
        image.save(f"public/images/{name}.jpg")
        result["generated image"] = f"Path of the Image='/images/{name}.jpg'"
        path["path"] = f"/images/{name}.jpg"
        result["predicted"] = predicted

    if task == "object-detection":
        img_url = data["image"]
        img_data = image_to_bytes(img_url)
        predicted = inference(data=img_data)
        image = Image.open(BytesIO(img_data))
        draw = ImageDraw.Draw(image)
        labels = list(item['label'] for item in predicted)
        color_map = {}
        for label in labels:
            if label not in color_map:
                color_map[label] = (random.randint(0, 255), random.randint(0, 100), random.randint(0, 255))
        for label in predicted:
            box = label["box"]
            draw.rectangle(((box["xmin"], box["ymin"]), (box["xmax"], box["ymax"])), outline=color_map[label["label"]],
                           width=2)
            draw.text((box["xmin"] + 5, box["ymin"] - 15), label["label"], fill=color_map[label["label"]])
        name = str(uuid.uuid4())[:4]
        image.save(f"public/images/{name}.jpg")
        result["generated image"] =f"Path of the Image='/images/{name}.jpg'"
        result["path"] = f"/images/{name}.jpg"
        result["predicted"] = predicted

    if task in ["image-classification"]:
        img_url = data["image"]
        img_data = image_to_bytes(img_url)
        result = inference(data=img_data)

    if task == "image-to-text":
        img_url = data["image"]
        img_data = image_to_bytes(img_url)
        HUGGINGFACE_HEADERS["Content-Length"] = str(len(img_data))
        r = requests.post(task_url, headers=HUGGINGFACE_HEADERS, data=img_data, proxies=PROXY)
        result = {}
        if "generated_text" in r.json()[0]:
            result["generated text"] = r.json()[0].pop("generated_text")

    # AUDIO tasks
    if task == "text-to-speech":
        inference = InferenceApi(repo_id=model_id, token=os.getenv("LLAMA_TOKEN"))
        inputs = data["text"]
        response = inference(inputs, raw_response=True)
        # response = requests.post(task_url, headers=HUGGINGFACE_HEADERS, json={"inputs": text})
        name = str(uuid.uuid4())[:4]
        with open(f"public/audios/{name}.flac", "wb") as f:
            f.write(response.content)
        result["generated audio"]=f"/audios/{name}.flac"
        path["path"] = f"/audios/{name}.flac"
    if task in ["automatic-speech-recognition", "audio-to-audio", "audio-classification"]:
        inference = InferenceApi(repo_id=model_id, token=os.getenv("LLAMA_TOKEN"))
        audio_url = data["audio"]
        audio_data = requests.get(audio_url, timeout=10).content
        response = inference(data=audio_data, raw_response=True)
        result = response.json()
        if task == "audio-to-audio":
            content = None
            type = None
            for k, v in result[0].items():
                if k == "blob":
                    content = base64.b64decode(v.encode("utf-8"))
                if k == "content-type":
                    type = "audio/flac".split("/")[-1]
            audio = AudioSegment.from_file(BytesIO(content))
            name = str(uuid.uuid4())[:4]
            audio.export(f"public/audios/{name}.{type}", format=type)
            result["generated audio"] =f"Path of the Audio='/audios/{name}.{type}'"
            path["path"] = f"/audios/{name}.{type}"
    return result,path

def get_model_status(model_id, url, headers, queue = None):
    endpoint_type = "huggingface"
    r = requests.get(url, headers=headers, proxies=PROXY)
    if r.status_code == 200:
        if queue:
            queue.put((model_id, True, endpoint_type))
        return True
    else:
        if queue:
            queue.put((model_id, False, endpoint_type))
        return False
def extract_json_from_string(input_str):
    # Simplified regular expression pattern to identify JSON-like structures
    json_pattern = r'\{.*?\}'

    # Find all matches in the input string
    matches = re.findall(json_pattern, input_str, re.DOTALL)

    # List to store valid JSON objects
    json_objects = []

    for match in matches:
        try:
            # Attempt to load the match as a JSON object
            json_obj = json.loads(match)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # If it's not a valid JSON, skip it
            continue

    return json_objects

def get_avaliable_models(candidates, topk=5):
    all_available_models = {"local": [], "huggingface": []}
    threads = []
    result_queue = Queue()

    for candidate in candidates:
        model_id = candidate["id"]

        if inference_mode != "local":
            huggingfaceStatusUrl = f"https://api-inference.huggingface.co/status/{model_id}"
            thread = threading.Thread(target=get_model_status,
                                      args=(model_id, huggingfaceStatusUrl, HUGGINGFACE_HEADERS, result_queue))
            threads.append(thread)
            thread.start()

        if inference_mode != "huggingface" and config["local_deployment"] != "minimal":
            localStatusUrl = f"{Model_Server}/status/{model_id}"
            thread = threading.Thread(target=get_model_status, args=(model_id, localStatusUrl, {}, result_queue))
            threads.append(thread)
            thread.start()

    result_count = len(threads)
    while result_count:
        model_id, status, endpoint_type = result_queue.get()
        if status and model_id not in all_available_models:
            all_available_models[endpoint_type].append(model_id)
        if len(all_available_models["local"] + all_available_models["huggingface"]) >= topk:
            break
        result_count -= 1

    for thread in threads:
        thread.join()

    return all_available_models

def run_task(input, command, results,path=None):
    id = command["id"]
    args = command["args"]
    task = command["task"]
    deps = command["dep"]

    if deps[0] != -1:
        dep_tasks = [results[dep] for dep in deps]
    else:
        dep_tasks = []

    logger.debug(f"Run task: {id} - {task}")
    logger.debug("Deps: " + json.dumps(dep_tasks))

    if deps[0] != -1:
        if "image" in args and "<GENERATED>-" in args["image"]:
            resource_id = int(args["image"].split("-")[1])
            if "generated image" in results[resource_id]["inference result"]:
                args["image"] = results[resource_id]["inference result"]["generated image"]
        if "audio" in args and "<GENERATED>-" in args["audio"]:
            resource_id = int(args["audio"].split("-")[1])
            if "generated audio" in results[resource_id]["inference result"]:
                args["audio"] = results[resource_id]["inference result"]["generated audio"]
        if "text" in args and "<GENERATED>-" in args["text"]:
            resource_id = int(args["text"].split("-")[1])
            if "generated text" in results[resource_id]["inference result"]:
                args["text"] = results[resource_id]["inference result"]["generated text"]


    text = image = audio = None
    for dep_task in dep_tasks:
        if "generated text" in dep_task["inference result"]:
            text = dep_task["inference result"]["generated text"]
            logger.debug("Detect the generated text of dependency task (from results):" + text)
        elif "text" in dep_task["task"]["args"]:
            text = dep_task["task"]["args"]["text"]
            logger.debug("Detect the text of dependency task (from args): " + text)
        if "generated image" in dep_task["inference result"]:
            image = dep_task["inference result"]["generated image"]
            logger.debug("Detect the generated image of dependency task (from results): " + image)
        elif "image" in dep_task["task"]["args"]:
            image = dep_task["task"]["args"]["image"]
            logger.debug("Detect the image of dependency task (from args): " + image)
        if "generated audio" in dep_task["inference result"]:
            audio = dep_task["inference result"]["generated audio"]
            logger.debug("Detect the generated audio of dependency task (from results): " + audio)
        elif "audio" in dep_task["task"]["args"]:
            audio = dep_task["task"]["args"]["audio"]
            logger.debug("Detect the audio of dependency task (from args): " + audio)

    if "image" in args and "<GENERATED>" in args["image"]:
        if image:
            args["image"] = image
    if "audio" in args and "<GENERATED>" in args["audio"]:
        if audio:
            args["audio"] = audio
    if "text" in args and "<GENERATED>" in args["text"]:
        if text:
            args["text"] = text

    for resource in ["image", "audio"]:
        if resource in args and not args[resource].startswith("public/") and len(args[resource]) > 0 and not args[resource].startswith("http"):
            args[resource] = f"public/{args[resource]}"

    if "-text-to-image" in command['task'] and "text" not in args:
        logger.debug("control-text-to-image task, but text is empty, so we use control-generation instead.")
        control = task.split("-")[0]

        if control == "seg":
            task = "image-segmentation"
            command['task'] = task
        elif control == "depth":
            task = "depth-estimation"
            command['task'] = task
        else:
            task = f"{control}-control"

    command["args"] = args
    logger.debug(f"parsed task: {command}")

    if task in ["summarization", "translation", "conversational", "text-generation",
                "text2text-generation"]:  # ChatGPT Can do
        best_model_id = "LLAMA3-8B"
        reason = "LLAMA3-8B performs well on some NLP tasks as well."
        choose = {"id": best_model_id, "reason": reason}
        messages = [{
            "role": "user",
            "content": f"[ {input} ] contains a task in JSON format {command}. Now you are a {command['task']} system, the arguments are {command['args']}. Just help me do {command['task']} and give me the result. The result must be in text form without any urls."
        }]
        response = chitchat(messages)
        results[id] = collect_result(command, choose, {"response": response})
        return True
    else:
        if task not in MODELS_MAP:
            logger.warning(f"no available models on {task} task.")
            record_case(success=False,
                        **{"input": input, "task": command, "reason": f"task not support: {command['task']}",
                           "op": "message"})
            inference_result = {"error": f"{command['task']} not found in available tasks."}
            results[id] = collect_result(command, "", inference_result)
            return False

        candidates = MODELS_MAP[task][:10]
        all_avaliable_models = get_avaliable_models(candidates, config["num_candidate_models"])
        all_avaliable_model_ids = all_avaliable_models["local"] + all_avaliable_models["huggingface"]
        logger.debug(f"avaliable models on {command['task']}: {all_avaliable_models}")

        if len(all_avaliable_model_ids) == 0:
            logger.warning(f"no available models on {command['task']}")
            record_case(success=False,
                        **{"input": input, "task": command, "reason": f"no available models: {command['task']}",
                           "op": "message"})
            inference_result = {"error": f"no available models on {command['task']} task."}
            #inference_result=model_api.generate(prompt=f"{inference_result['error']}").response
            results[id] = collect_result(command, "", inference_result)
            return False

        if len(all_avaliable_model_ids) == 1:
            best_model_id = all_avaliable_model_ids[0]
            reason = "Only one model available."
            choose = {"id": best_model_id, "reason": reason}
            logger.debug(f"chosen model: {choose}")
        else:
            cand_models_info = [
                {
                    "id": model["id"],
                    "inference endpoint": all_avaliable_models.get(
                        "local" if model["id"] in all_avaliable_models["local"] else "huggingface"
                    ),
                    "likes": model.get("likes"),
                    "description": model.get("description", "")[:config["max_description_length"]],
                    # "language": model.get("meta").get("language") if model.get("meta") else None,
                    "tags": model.get("meta").get("tags") if model.get("meta") else None,
                }
                for model in candidates
                if model["id"] in all_avaliable_model_ids
            ]

            choose_str = choose_model(input, command, cand_models_info)
            logger.debug(f"chosen model: {choose_str}")
            try:
                choose = json.loads(choose_str)
                best_model_id = choose["id"]
            except Exception as e:
                choose=extract_json_from_string(choose_str)
                best_model_id = choose[0]["id"]
                if choose==[]:
                    logger.warning(
                        f"the response [ {choose_str} ] is not a valid JSON, try to find the model id and reason in the response.")
                    choose_str = find_json(choose_str)
                    best_model_id, reason, choose = get_id_reason(choose_str)
        inference_result ,path= huggingface_model_inference(best_model_id, args, command['task'],path=path)
        if "error" in inference_result:
            logger.warning(f"Inference error: {inference_result['error']}")
            record_case(success=False,
                        **{"input": input, "task": command, "reason": f"inference error: {inference_result['error']}",
                           "op": "message"})
            results[id] = collect_result(command, choose, inference_result)
            return False

        results[id] = collect_result(command, choose, inference_result)
        return True


def extract_lists(input_str):
    # Regular expression to find JSON-like lists within the string
    # This regex looks for lists in the format: [{"key1": "value1", "key2": "value2"}, {...}]
    list_pattern = r'\[\s*{.*?}\s*\]'

    # Find all matches of the pattern
    matches = re.findall(list_pattern, input_str, re.DOTALL)

    # If matches are found, process them into lists
    result = []
    for match in matches:
        # Attempt to parse the match as JSON
        try:
            json_obj = json.loads(match)
            result.append(json_obj)
        except json.JSONDecodeError:
            continue

    return result

def chat_huggingface(messages, return_planning = False, return_results = False):
    start = time.time()
    context = messages[:-1]
    inputs = messages[-1]["content"]
    logger.info("*" * 80)
    logger.info(f"input: {inputs}")

    task_str = parse_task(context, inputs)
    try:
        tasks=extract_lists(task_str)[0]
    except IndexError as e:
        tasks=[]
    if tasks == []:  # using LLM response for empty task
        record_case(success=False,
                    **{"input": inputs, "task": [], "reason": "task parsing fail: empty", "op": "chitchat"})
        response = chitchat(messages)
        return {"message": response}

    if len(tasks) == 1 and tasks[0]["task"] in ["summarization", "conversational", "text-generation",
                                                "text2text-generation"]:
        record_case(success=True, **{"input": inputs, "task": tasks, "reason": "chitchat tasks", "op": "chitchat"})
        response = chitchat(messages)
        return {"message": response}
    if len(tasks)==1:
        record_case(success=True, **{"input": inputs, "task": tasks, "reason": "Single  tasks", "op": tasks[0]['task']})
        d=dict()
        path=dict
        done=run_task(inputs,tasks[0],d,path)
        if done:
            results=d.copy()
            paths=path.copy()
            response=response_results(inputs,results).strip()
            return {'message':response,"path":paths}
    tasks = unfold(tasks)
    tasks = fix_dep(tasks)
    logger.debug(tasks)

    if return_planning:
        return tasks

    results = {}
    threads = []
    tasks = tasks[:]
    d = dict()
    retry = 0
    while True:
        num_thread = len(threads)
        for task in tasks:
            # logger.debug(f"d.keys(): {d.keys()}, dep: {dep}")
            for dep_id in task["dep"]:
                if dep_id >= task["id"]:
                    task["dep"] = [-1]
                    break
            dep = task["dep"]
            if dep[0] == -1 or len(list(set(dep).intersection(d.keys()))) == len(dep):
                tasks.remove(task)
                thread = threading.Thread(target=run_task, args=(inputs, task, d))
                thread.start()
                threads.append(thread)
        if num_thread == len(threads):
            time.sleep(0.5)
            retry += 1
        if retry > 160:
            logger.debug("User has waited too long, Loop break.")
            break
        if len(tasks) == 0:
            break
        for thread in threads:
            thread.join()

        results = d.copy()
        logger.debug(results)
        if return_results:
            return results
        response = response_results(inputs, results).strip()

        end = time.time()
        during = end - start

        answer = {"message": response}
        record_case(success=True,
                    **{"input": inputs, "task": task_str, "results": results, "response": response, "during": during,
                       "op": "response"})
        logger.info(f"response: {response}")
        return answer
def task_planning(messages):
    context = messages[:-1]
    input = messages[-1]["content"]
    logger.info("*" * 80)
    logger.info(f"input: {input}")

    task_str = parse_task(context, input)
    try:
        tasks = extract_lists(task_str)[0]
    except IndexError as e:
        tasks = []

    tasks = unfold(tasks)
    tasks = fix_dep(tasks)
    logger.debug(tasks)
    return tasks

def results(tasks):
    results = {}
    threads = []
    tasks = tasks[:]
    d = dict()
    retry = 0
    while True:
        num_thread = len(threads)
        for task in tasks:
            # logger.debug(f"d.keys(): {d.keys()}, dep: {dep}")
            for dep_id in task["dep"]:
                if dep_id >= task["id"]:
                    task["dep"] = [-1]
                    break
            dep = task["dep"]
            if dep[0] == -1 or len(list(set(dep).intersection(d.keys()))) == len(dep):
                tasks.remove(task)
                thread = threading.Thread(target=run_task, args=(input, task, d))
                thread.start()
                threads.append(thread)
        if num_thread == len(threads):
            time.sleep(0.5)
            retry += 1
        if retry > 160:
            logger.debug("User has waited too long, Loop break.")
            break
        if len(tasks) == 0:
            break
        for thread in threads:
            thread.join()

        results = d.copy()
        logger.debug(results)
        return results

def cli():
    messages = []
    print("Welcome to Jarvis! A collaborative system that consists of an LLM as the controller and numerous expert models as collaborative executors. Jarvis can plan tasks, schedule Hugging Face models, generate friendly responses based on your requests, and help you with many things. Please enter your request (`exit` to exit).")
    while True:
        message = input("[ User ]: ")
        if message == "exit":
            break
        messages.append({"role": "user", "content": message})
        answer = chat_huggingface(messages,  return_planning=False, return_results=False)
        ans=answer['message']
        print("[ Jarvis ]: ", ans)
        messages.append({"role": "assistant", "content": answer["message"]})


if __name__=="__main__":
    cli()
