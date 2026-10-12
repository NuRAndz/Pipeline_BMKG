import json
from datetime import datetime, timezone
from pathlib import Path

import requests

FEEDS = ["autogempa", "gempaterkini", "gempadirasakan"]


def ambil_feed(feed):
    url = f"https://data.bmkg.go.id/DataMKG/TEWS/{feed}.json"
    folder = Path("data/raw/bmkg") / feed
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    folder.mkdir(parents=True, exist_ok=True)
    waktu = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{feed}_{waktu}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(feed, "tersimpan:", path)


def main():
    for feed in FEEDS:
        ambil_feed(feed)


if __name__ == "__main__":
    main()