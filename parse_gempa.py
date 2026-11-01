import hashlib
import json
from pathlib import Path
import pandas as pd


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
    semua_baris = []

    # Baca SEMUA file JSON di semua folder feed
    for file in sorted(Path("data/raw/bmkg").glob("*/*.json")):
        feed = file.parent.name  # nama folder = nama feed
        for item in baca_gempa(file):
            semua_baris.append(bersihkan(item, feed))

    df = pd.DataFrame(semua_baris)
    print("Sebelum dedup:", len(df))

    # Gabungkan isi dari semua baris dengan event_id yang sama
    df = df.groupby("event_id", as_index=False).first()
    print("Setelah dedup:", len(df))
    print("Potensi terisi:", df["potensi"].notna().sum(),
          "| Dirasakan terisi:", df["dirasakan"].notna().sum())

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/gempa.csv", index=False)
    print("Tersimpan: data/processed/gempa.csv")


if __name__ == "__main__":
    main()