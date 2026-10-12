import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

FEEDS = ["autogempa", "gempaterkini", "gempadirasakan"]
MAKS_PERCOBAAN = 3
JEDA_DETIK = 5


def ambil_feed(feed):
    url = f"https://data.bmkg.go.id/DataMKG/TEWS/{feed}.json"
    folder = Path("data/raw/bmkg") / feed

    # Coba beberapa kali sebelum menyerah (server BMKG kadang lambat)
    for percobaan in range(1, MAKS_PERCOBAAN + 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            break
        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"{feed}: percobaan {percobaan}/{MAKS_PERCOBAAN} gagal ({error})")
            if percobaan == MAKS_PERCOBAAN:
                raise
            time.sleep(JEDA_DETIK)

    folder.mkdir(parents=True, exist_ok=True)
    waktu = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{feed}_{waktu}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(feed, "tersimpan:", path)


def main():
    gagal = []

    for feed in FEEDS:
        try:
            ambil_feed(feed)
        except Exception as error:
            # Satu feed gagal tidak boleh menghentikan feed lainnya
            print(f"{feed}: GAGAL ({error})")
            gagal.append(feed)

    if gagal:
        print("Feed yang gagal:", ", ".join(gagal))

    # Kalau semua gagal, akhiri dengan kode error supaya GitHub menandai run ini merah
    if len(gagal) == len(FEEDS):
        sys.exit(1)


if __name__ == "__main__":
    main()