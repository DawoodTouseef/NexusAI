import yaml
import os
import logging
from Server.get_token_ids import *
import re
import json
import io
import traceback
import copy
from diffusers.utils import load_image
from huggingface_hub import InferenceClient
from ollama_python.endpoints.generate import GenerateAPI
from dotenv import load_dotenv
import time
import threading

load_dotenv()
config_file = "configs/config.yaml"
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
model_api=GenerateAPI(model="openchat_3.5")
LLM_encoding = LLM
if config["dev"] and LLM == "mistral-7b-instruct-v0.1":
    LLM_encoding = "mistral-7b-instruct-v0.1"
task_parsing_highlight_ids = get_token_ids_for_task_parsing(LLM_encoding)
choose_model_highlight_ids = get_token_ids_for_choose_model(LLM_encoding)

MODELS = [json.loads(line) for line in open("data/p0_models.jsonl", "r").readlines()]
MODELS_MAP = {}
for model in MODELS:
    tag = model["task"]
    if tag not in MODELS_MAP:
        MODELS_MAP[tag] = []
    MODELS_MAP[tag].append(model)

METADATAS = {}
for model in MODELS:
    METADATAS[model["id"]] = model

parse_task_demos_or_presteps = open(config["demos_or_presteps"]["parse_task"], "r").read()
choose_model_demos_or_presteps = open(config["demos_or_presteps"]["choose_model"], "r").read()
response_results_demos_or_presteps = open(config["demos_or_presteps"]["response_results"], "r").read()

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
        print(e)
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
    print(data)
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


def collect_result(command, choose, inference_result):
    result = {"task": command}
    result["inference result"] = inference_result
    result["choose model result"] = choose
    logger.debug(f"inference result: {inference_result}")
    return result

def models(task,id,query:str):
    if task in ["text-classification", "token-classification", "text2text-generation", "summarization", "translation",
                "conversational", "text-generation"]:
        model=GenerateAPI(model="phi3")
        responses=model.generate(prompt=query,options={"num_predict":4096})

    if task == "question-answering":
        model=GenerateAPI(model="llama3")
        responses=model.generate(prompt=query,options={"num_predict":8092})

    return responses

def run_task(input, command, results):
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
        if resource in args and not args[resource].startswith("public/") and len(args[resource]) > 0 and not args[
            resource].startswith("http"):
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
        reason = "ChatGPT performs well on some NLP tasks as well."
        choose = {"id": best_model_id, "reason": reason}
        messages = [{
            "role": "user",
            "content": f"[ {input} ] contains a task in JSON format {command}. Now you are a {command['task']} system, the arguments are {command['args']}. Just help me do {command['task']} and give me the result. The result must be in text form without any urls."
        }]
        response = chitchat(messages)
        results[id] = collect_result(command, choose, {"response": response})
        return True


def extract_lists(input_str):
    # Regular expression to find JSON-like lists within the string
    # This regex looks for lists in the format: [{"key1": "value1", "key2": "value2"}, {...}]
    list_pattern = r'\[(\{.*?\})+\]'

    # Find all matches of the pattern
    matches = re.findall(list_pattern, input_str, re.DOTALL)

    # If matches are found, process them into lists
    result = []
    for match in matches:
        # Remove newlines and extra spaces
        clean_match = match.replace('\n', '').replace(' ', '')
        # Add the cleaned match to result list
        result.append(clean_match)

    return result

def chat_huggingface(messages, return_planning = False, return_results = False):
    start = time.time()
    context = messages[:-1]
    input = messages[-1]["content"]
    logger.info("*" * 80)
    logger.info(f"input: {input}")

    task_str = parse_task(context, input)
    tasks=extract_lists(task_str)

    if task_str == {}:  # using LLM response for empty task
        record_case(success=False, **{"input": input, "task": [], "reason": "task parsing fail: empty", "op": "chitchat"})
        response = chitchat(messages)
        return {"message": response}

    if len(tasks) == 1 and tasks[0]["task"] in ["summarization", "translation", "conversational", "text-generation", "text2text-generation"]:
        record_case(success=True, **{"input": input, "task": tasks, "reason": "chitchat tasks", "op": "chitchat"})
        response = chitchat(messages)
        return {"message": response}

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
    if return_results:
        return results

    response = response_results(input, results).strip()

    end = time.time()
    during = end - start

    answer = {"message": response}
    record_case(success=True,
                **{"input": input, "task": task_str, "results": results, "response": response, "during": during,
                   "op": "response"})
    logger.info(f"response: {response}")
    return answer
