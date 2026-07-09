"""measure read latency on both backends under repeated point lookups.

runs the same "one year, one major" query N times against rds and dynamodb
and reports average latency. requires the backends to be provisioned and
loaded (see scripts/), plus rds credentials in the environment.
"""

import os
import time
import urllib.parse
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from tqdm import tqdm

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
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


def test_rds_latency(engine, iterations: int = 100):
    print(f"\ntesting rds (mysql) performance [{iterations} requests]")
    query = (
        "select * from enrollment_stats "
        "where academic_year = 2024 and major_name = 'computer science'"
    )
    start = time.time()
    for _ in tqdm(range(iterations), desc="rds progress", unit="req", colour="blue"):
        pd.read_sql(query, con=engine)
    return (time.time() - start) / iterations


def test_dynamo_latency(table, iterations: int = 100):
    print(f"\ntesting dynamodb performance [{iterations} requests]")
    start = time.time()
    for _ in tqdm(range(iterations), desc="dynamo progress", unit="req", colour="red"):
        table.get_item(Key={"academic_year": 2024, "major_name": "computer science"})
    return (time.time() - start) / iterations


def main(count: int = 100) -> None:
    print("starting automated database stress test")
    engine = _rds_engine()
    table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DYNAMO_TABLE)

    rds_speed = test_rds_latency(engine, count)
    dynamo_speed = test_dynamo_latency(table, count)

    print("\n" + "=" * 30)
    print("      final results")
    print("=" * 30)
    print(f"rds avg latency:    {rds_speed:.4f}s")
    print(f"dynamo avg latency: {dynamo_speed:.4f}s")
    print("=" * 30)


if __name__ == "__main__":
    main(100)  # 100 or 1000 requests
