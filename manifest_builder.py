import os, json, requests, datetime, sys

# ---------------- Env / Defaults ----------------
GH_TOKEN   = os.getenv("GH_TOKEN", "").strip()           # optional
FW_REPOS   = [r.strip() for r in os.getenv("FW_REPOS", "").split(",") if r.strip()]  # optional
FW_CHANNEL = os.getenv("FW_CHANNEL", "stable")

OUT_DIR    = os.getenv("FW_OUT_DIR", ".").strip() or "."
OUT_FILE   = os.getenv("FW_OUT_FILE", "firmware.json").strip() or "firmware.json"

# ---------------- HTTP Session ------------------
S = requests.Session()
S.headers.update({"Accept": "application/vnd.github+json"})
if GH_TOKEN:
    S.headers.update({"Authorization": f"Bearer {GH_TOKEN}"})


def latest_release(owner_repo: str):
    """
    Liefert das neueste Release-JSON oder None.
    Überspringt sauber bei 404 (keine Releases) oder Netzwerk-/RateLimit-Fehlern.
    """
    url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    try:
        r = S.get(url, timeout=20)
        if r.status_code == 404:
            return None  # noch kein Release
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def choose_first_bin_asset(rel: dict):
    """Nimmt das erste .bin-Asset in einem Release, sonst None."""
    if not rel:
        return None
    for a in rel.get("assets", []):
        if str(a.get("name", "")).endswith(".bin"):
            return a
    return None


def build_manifest():
    devices = []

    for repo in FW_REPOS:
        rel = latest_release(repo)
        if not rel:
            # Kein Release vorhanden oder API-Fehler -> Repo ignorieren
            continue

        asset = choose_first_bin_asset(rel)
        if not asset:
            # Release ohne .bin -> ignorieren
            continue

        tag = str(rel.get("tag_name") or "")
        version = tag.lstrip("v") if tag else "0.0.0"

        name = asset.get("name", "")
        url  = asset.get("browser_download_url", "")
        size = int(asset.get("size", 0) or 0)

        # Device-ID aus Dateinamen bis zum ersten "_" (Fallback: Repo-Name)
        device_id = name.split("_")[0] if "_" in name and name.split("_")[0] else repo.split("/")[-1]

        devices.append({
            "id": device_id,
            "name": device_id.capitalize(),
            "version": version,
            "url": url,
            "filesize": size,
            "sha256": "",                 # optional: später befüllen (Hashprüfung)
            "min_app_version": "1.0.0",
            "critical": False
        })

    manifest = {
        "schema": 1,
        "channel": FW_CHANNEL,
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "devices": devices
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[manifest] wrote {out_path} with {len(devices)} device(s).")
    return 0


if __name__ == "__main__":
    sys.exit(build_manifest())