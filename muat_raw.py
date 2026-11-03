from pathlib import Path

import pandas as pd
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from parse_gempa import baca_gempa

TABEL_RAW = "pipeline-bmkg.bmkg.gempa_raw"

KOLOM = ["feed", "nama_file", "waktu_ambil",
         "Tanggal", "Jam", "DateTime", "Coordinates", "Lintang", "Bujur",
         "Magnitude", "Kedalaman", "Wilayah", "Potensi", "Dirasakan", "Shakemap"]

# Path relatif terhadap lokasi skrip, bukan folder tempat perintah dijalankan
FOLDER_PROYEK = Path(__file__).parent
FOLDER_RAW = FOLDER_PROYEK / "data/raw/bmkg"


def baca_semua_raw():
    semua_baris = []
    for file in sorted(FOLDER_RAW.glob("*/*.json")):
        feed = file.parent.name  # nama subfolder = nama feed
        # "autogempa_20261031T172529Z" -> format sama dengan ambil_gempa.py
        waktu_ambil = pd.to_datetime(file.stem.split("_")[-1], format="%Y%m%dT%H%M%SZ", utc=True)
        for item in baca_gempa(file):
            # Data asli BMKG tidak diubah, hanya ditambah metadata
            semua_baris.append({**item, "feed": feed, "nama_file": file.name, "waktu_ambil": waktu_ambil})
    return pd.DataFrame(semua_baris).reindex(columns=KOLOM)


def file_sudah_dimuat(client):
    try:
        hasil = client.query(f"SELECT DISTINCT nama_file FROM `{TABEL_RAW}`").to_dataframe()
        return set(hasil["nama_file"])
    except NotFound:
        return set()  # tabel belum ada -> belum ada file yang dimuat


def main():
    df = baca_semua_raw()
    print("Baris di file lokal:", len(df))

    client = bigquery.Client.from_service_account_json(FOLDER_PROYEK / "service-account.json")
    sudah = file_sudah_dimuat(client)
    df = df[~df["nama_file"].isin(sudah)].copy()
    print("File baru yang akan dimuat:", df["nama_file"].nunique(), "| baris:", len(df))

    if df.empty:
        print("Tidak ada file baru. Selesai.")
        return

    # NaN (float) bikin load gagal; tipe string mengubahnya jadi <NA> -> NULL di BigQuery
    for kolom in KOLOM:
        if kolom != "waktu_ambil":
            df[kolom] = df[kolom].astype("string")

    schema = [
        bigquery.SchemaField(k, "TIMESTAMP" if k == "waktu_ambil" else "STRING")
        for k in KOLOM
    ]
    job_config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_APPEND")
    client.load_table_from_dataframe(df, TABEL_RAW, job_config=job_config).result()
    print("Tersimpan ke", TABEL_RAW)


if __name__ == "__main__":
    main()
