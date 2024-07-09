from huggingface_hub import HfApi,hf_hub_download
import json

def get_model(repo_id,MODEL,local_dir="hf_cache"):
    api=HfApi()
    models = api.model_info(repo_id=repo_id)
    modelss = {"downloads": models.downloads, "id": models.id, "likes": models.likes, "pipeline_tag": models.pipeline_tag,
               "task": models.pipeline_tag,
               "meta": {"language": models.card_data.language, "tags": models.tags, "widget": models.widget_data},}
    for model in models.siblings:
        if model.rfilename=="README.md":
            file_path = hf_hub_download(repo_id=repo_id, filename=model.rfilename, local_dir=local_dir)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                modelss.update({"description": content})
            MODEL.append(modelss)
            with open("/home/lenovo/NexusAI/Server/data/p1_models.jsonl","w") as f:
                for i in MODEL:
                    json_lines=json.dumps(i)
                    f.write(json_lines + '\n')
            print("Done")

if __name__=="__main__":
    MODELS = [json.loads(line) for line in open("/home/lenovo/NexusAI/Server/data/p0_models.jsonl", "r").readlines()]
    get_model("microsoft/Florence-2-base",MODELS)