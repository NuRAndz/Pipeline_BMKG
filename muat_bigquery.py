from pathlib import Path

import pandas as pd
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

TABEL = "pipeline-bmkg.bmkg.gempa"

# Path relatif terhadap lokasi skrip, bukan folder tempat perintah dijalankan
FOLDER_PROYEK = Path(__file__).parent

KOLOM_TEKS = ["event_id", "feed", "wilayah", "potensi", "dirasakan"]

SCHEMA = [
    bigquery.SchemaField("event_id", "STRING"),
    bigquery.SchemaField("feed", "STRING"),
    bigquery.SchemaField("waktu_utc", "TIMESTAMP"),
    bigquery.SchemaField("lintang", "FLOAT"),
    bigquery.SchemaField("bujur", "FLOAT"),
    bigquery.SchemaField("magnitudo", "FLOAT"),
    bigquery.SchemaField("kedalaman_km", "FLOAT"),
    bigquery.SchemaField("wilayah", "STRING"),
    bigquery.SchemaField("potensi", "STRING"),
    bigquery.SchemaField("dirasakan", "STRING"),
]


def main():
    client = bigquery.Client.from_service_account_json(FOLDER_PROYEK / "service-account.json")

    baru = pd.read_csv(FOLDER_PROYEK / "data/processed/gempa.csv")
    baru["waktu_utc"] = pd.to_datetime(baru["waktu_utc"], utc=True)
    print("Data baru:", len(baru))

    try:
        lama = client.query(f"SELECT * FROM `{TABEL}`").to_dataframe()
    except NotFound:
        lama = pd.DataFrame()  # tabel belum ada -> belum ada data lama
    print("Data lama di BigQuery:", len(lama))

    # baru di depan supaya first() memprioritaskan nilai terbaru
    gabungan = pd.concat([baru, lama], ignore_index=True)
    gabungan = gabungan.groupby("event_id", as_index=False).first()
    print("Setelah gabung + dedup:", len(gabungan))

    # Kolom yang seluruhnya kosong dibaca pandas sebagai NaN (float); jadikan teks -> NULL di BigQuery
    for kolom in KOLOM_TEKS:
        gabungan[kolom] = gabungan[kolom].astype("string")

    job_config = bigquery.LoadJobConfig(schema=SCHEMA, write_disposition="WRITE_TRUNCATE")
    client.load_table_from_dataframe(gabungan[[f.name for f in SCHEMA]], TABEL, job_config=job_config).result()
    print("Tersimpan ke", TABEL)


if __name__ == "__main__":
    main()
