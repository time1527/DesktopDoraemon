import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download
from settings import DEFAULT_MODEL_STORAGE_PATH

def download_model(model_name):
    snapshot_download(
       repo_id = model_name,
       local_dir = DEFAULT_MODEL_STORAGE_PATH / model_name,
       resume_download=True)

if __name__ == "__main__":
  model_name = "jinaai/jina-embeddings-v3"
  download_model(model_name)
