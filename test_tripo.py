import os, time, requests, sys

API_KEY = "tsk_IgxudylWsvXGWs6oizkypsu2AU1GsWzQac8gs7gcRrD"
BASE = "https://api.tripo3d.ai/v2/openapi"
HDRS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def create_text_task(prompt: str, model_version="v2.0-20240919", texture=True, pbr=True):
    payload = {
        "type": "text_to_model",   # task type per Tripo OpenAPI
        "prompt": prompt,
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr
    }
    r = requests.post(f"{BASE}/task", json=payload, headers=HDRS, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Create task error: {data}")
    return data["data"]["task_id"]

def get_task(task_id: str):
    r = requests.get(f"{BASE}/task/{task_id}", headers=HDRS, timeout=60)
    r.raise_for_status()
    return r.json()

def download(url: str, out_path: str):
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return out_path

if __name__ == "__main__":
    prompt = "a stylized low-poly shiba inu figurine"
    print("Submitting task…")
    task_id = create_text_task(prompt)
    print("Task ID:", task_id)

    print("Polling… (this can take ~tens of seconds)")
    while True:
        info = get_task(task_id)
        # Tripo’s responses use a unified structure with a `code` and a data payload.
        # Status is typically one of: queued/running/success/failed (naming may vary slightly)
        # and outputs appear under data.output.* when ready. :contentReference[oaicite:1]{index=1}
        if info.get("code") != 0:
            print("Error:", info)
            sys.exit(1)
        status = info["data"]["status"]
        if status in ("success", "succeeded", "SUCCESS"):
            out = info["data"]["output"]
            # Common fields you may see:
            #   out["model"]      -> GLB
            #   out.get("pbr_model") -> GLB with PBR
            #   out.get("rendered_image") -> preview
            model_url = out.get("pbr_model") or out.get("model")
            if not model_url:
                print("No model URL found in output:", out)
                sys.exit(1)
            print("Downloading:", model_url)
            path = download(model_url, "tripo_model.glb")
            print("Saved:", path)
            break
        elif status in ("failed", "error"):
            print("Task failed:", info)
            sys.exit(1)
        time.sleep(3)

