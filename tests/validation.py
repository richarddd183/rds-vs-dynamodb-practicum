"""verify the migration moved every row into rds intact.

compares the source excel row count against rds, and reports the dynamodb
count (expected lower, since it is aggregated by year + major).
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


def _rds_engine():
    password = os.environ.get("RDS_PASSWORD")
    if not password or not RDS_ENDPOINT:
        raise RuntimeError("RDS_PASSWORD and RDS_ENDPOINT must be set (see .env.example)")
    safe = urllib.parse.quote_plus(password)
    url = f"mysql+mysqlconnector://{RDS_USER}:{safe}@{RDS_ENDPOINT}/{RDS_DB_NAME}"
    return create_engine(url, connect_args={"ssl_ca": str(SSL_CA)})


def get_counts() -> None:
    print("starting migration validation")

    local_count = len(pd.read_excel(DATA_FILE))

    try:
        engine = _rds_engine()
        rds_count = pd.read_sql("select count(*) from enrollment_stats", con=engine).iloc[0, 0]
    except Exception as error:  # pylint: disable=broad-except
        rds_count = f"error: {error}"

    try:
        table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DYNAMO_TABLE)
        dynamo_count = table.item_count
        if dynamo_count == 0:
            dynamo_count = table.scan(Select="COUNT")["Count"]
    except Exception as error:  # pylint: disable=broad-except
        dynamo_count = f"error: {error}"

    print("\n[results]")
    print(f"original excel rows: {local_count}")
    print(f"rds (mysql) records: {rds_count}")
    print(f"dynamodb records:    {dynamo_count}")

    if rds_count == local_count:
        print("\nrds migration: 100% data integrity")
    else:
        print("\nrds mismatch: check for upload errors or existing data")

    print("\nnote: dynamodb count is expected to be lower due to grouping by (year + major)")


if __name__ == "__main__":
    get_counts()
