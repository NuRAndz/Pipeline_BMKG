import hashlib
import json
from pathlib import Path


def baca_gempa(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    gempa = data["Infogempa"]["gempa"]

    # Kalau cuma satu gempa (objek), bungkus jadi daftar berisi satu item
    if isinstance(gempa, dict):
        gempa = [gempa]

    return gempa


def buat_event_id(waktu_utc, lintang, bujur, magnitudo):
    # Gempa yang sama di feed berbeda menghasilkan ID yang sama
    teks = f"{waktu_utc}|{lintang:.2f}|{bujur:.2f}|{magnitudo:.1f}"
    return hashlib.sha1(teks.encode()).hexdigest()


def bersihkan(item, feed):
    # "Coordinates" berbentuk "-2.87,122.21" (lintang negatif = LS)
    lintang, bujur = item["Coordinates"].split(",")
    lintang = float(lintang)
    bujur = float(bujur)

    magnitudo = float(item["Magnitude"])

    # "Kedalaman" berbentuk "4 km" -> ambil angkanya saja
    kedalaman_km = float(item["Kedalaman"].split()[0])

    waktu_utc = item["DateTime"]

    return {
        "event_id": buat_event_id(waktu_utc, lintang, bujur, magnitudo),
        "feed": feed,
        "waktu_utc": waktu_utc,
        "lintang": lintang,
        "bujur": bujur,
        "magnitudo": magnitudo,
        "kedalaman_km": kedalaman_km,
        "wilayah": item["Wilayah"],
        # Tidak semua feed punya kolom ini
        "potensi": item.get("Potensi"),
        "dirasakan": item.get("Dirasakan"),
    }


def main():
    for feed in ["autogempa", "gempaterkini", "gempadirasakan"]:
        # Ambil file terbaru (nama file berisi timestamp, jadi urut waktu)
        file = sorted(Path(__file__).parent.joinpath("data/raw/bmkg", feed).glob("*.json"))[-1]
        daftar = baca_gempa(file)
        print(feed, "->", len(daftar), "gempa")
        print(bersihkan(daftar[0], feed))
        print()


if __name__ == "__main__":
    main()