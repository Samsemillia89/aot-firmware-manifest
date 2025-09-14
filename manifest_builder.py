import os, json, hashlib, requests, sys, datetime

GHTOKEN = os.environ["GH_TOKEN"]
REPOS = os.environ["FW_REPOS"].split(",")  # "Samsemillia89/AOT-Controller,Samsemillia89/AOT-Display"
CHANNEL = os.getenv("FW_CHANNEL", "stable")

S = requests.Session()
S.headers.update({"Authorization": f"Bearer {GHTOKEN}", "Accept": "application/vnd.github+json"})

def latest_release(owner_repo):
    r = S.get(f"https://api.github.com/repos/{owner_repo}/releases/latest")
    r.raise_for_status()
    return r.json()

def choose_asset(rel):
    # nimm erstes .bin Asset
    for a in rel.get("assets", []):
        if a["name"].endswith(".bin"):
            return a
    return None

def sha256_of_url(url):
    # nicht downloaden: GitHub liefert Content-Length, SHA machen wir optional (wenn gewünscht: streamen)
    return None

devices = []
for rr in REPOS:
    rel = latest_release(rr.strip())
    asset = choose_asset(rel)
    if not asset: 
        continue
    name = asset["name"]                        # z.B. controller_1.3.0.bin
    version = rel["tag_name"].lstrip("v")       # v1.3.0 -> 1.3.0
    url = asset["browser_download_url"]
    size = asset["size"]
    device_id = name.split("_")[0]              # vor dem ersten "_" -> "controller"

    devices.append({
        "id": device_id,
        "name": device_id.capitalize(),
        "version": version,
        "url": url,
        "filesize": size,
        "sha256": "",                           # optional, leer lassen oder in Zukunft befüllen
        "min_app_version": "1.0.0",
        "critical": False
    })

manifest = {
    "schema": 1,
    "channel": CHANNEL,
    "updated_at": datetime.datetime.utcnow().isoformat()+"Z",
    "devices": devices
}

with open("firmware.json", "w") as f:
    json.dump(manifest, f, indent=2)
print("Wrote firmware.json with", len(devices), "entries")