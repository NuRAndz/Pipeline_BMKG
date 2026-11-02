from google.api_core.exceptions import NotFound

TABEL = "pipeline-bmkg.bmkg.gempa"
client = bigquery.Client.from_service_account_json("service-account.json")

baru = pd.read_csv("data/processed.gempa.csv")
baru["waktu_utc"] = pd.to_datetime(baru["waktu_utc"], utc=True)

