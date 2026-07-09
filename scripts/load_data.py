"""load the merged enrollment data into both backends.

rds gets the full flat table; dynamodb gets rows aggregated by
(academic_year, major_name) to satisfy its composite key.
"""

import os
import urllib.parse
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "au-enrollment-merged.xlsx"
SSL_CA = ROOT / "certs" / "global-bundle.pem"

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "au_enrollment_stats")
RDS_USER = os.environ.get("RDS_USER", "admin")
RDS_ENDPOINT = os.environ.get("RDS_ENDPOINT", "")
RDS_DB_NAME = os.environ.get("RDS_DB_NAME", "enrollment")


def _rds_url() -> str:
    password = os.environ.get("RDS_PASSWORD")
    if not password or not RDS_ENDPOINT:
        raise RuntimeError("RDS_PASSWORD and RDS_ENDPOINT must be set (see .env.example)")
    safe = urllib.parse.quote_plus(password)
    return f"mysql+mysqlconnector://{RDS_USER}:{safe}@{RDS_ENDPOINT}/{RDS_DB_NAME}"


data_frame = pd.read_excel(DATA_FILE)
data_frame["academic_year"] = data_frame["academic_year"].apply(
    lambda x: int(str(x).split("-", maxsplit=1)[0])
)

# dynamodb needs unique (year, major) keys, so aggregate duplicates first
dynamo_df = (
    data_frame.groupby(["academic_year", "major_name"])
    .agg({"student_count": "sum", "department_name": "first"})
    .reset_index()
)


def upload_to_rds() -> None:
    try:
        engine = create_engine(_rds_url(), connect_args={"ssl_ca": str(SSL_CA)})
        data_frame.to_sql("enrollment_stats", con=engine, if_exists="append", index=False)
        print("rds upload successful")
    except Exception as error:  # pylint: disable=broad-except
        print(f"rds connection error: {error}")


def upload_to_dynamo() -> None:
    try:
        resource = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = resource.Table(DYNAMO_TABLE)
        with table.batch_writer() as batch:
            for _, row in dynamo_df.iterrows():
                batch.put_item(
                    Item={
                        "academic_year": int(row["academic_year"]),
                        "major_name": str(row["major_name"]),
                        "department_name": str(row["department_name"]),
                        "student_count": int(row["student_count"]),
                    }
                )
        print("dynamodb upload successful")
    except Exception as error:  # pylint: disable=broad-except
        print(f"dynamodb error: {error}")


if __name__ == "__main__":
    upload_to_rds()
    upload_to_dynamo()
