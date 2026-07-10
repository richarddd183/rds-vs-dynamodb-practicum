"""measure read latency on both backends under concurrent load.

the sibling performance_test.py issues requests one after another, which answers
"how fast is a single lookup". this script answers a different question: what
happens when many clients query at the same time.

that distinction matters. a serial run never reveals connection-pool contention
on rds, and never triggers dynamodb throttling, because it only ever has one
request in flight. results here are therefore not comparable to the serial
numbers in the readme, and are not meant to be.

each worker issues the same "one year, one major" point lookup. per-request
latency is recorded, then summarised as mean and p50/p95/p99, alongside
throughput and any errors. tail latency is the point: an average hides the
requests that a real user would notice.

requires both backends provisioned (see infra/) and loaded (see scripts/).

    python tests/concurrency_test.py --workers 50 --requests 1000
"""

import argparse
import json
import os
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import boto3
import numpy as np
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SSL_CA = ROOT / "certs" / "global-bundle.pem"
RESULTS = ROOT / "data" / "concurrency_results.json"

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "au_enrollment_stats")
RDS_USER = os.environ.get("RDS_USER", "admin")
RDS_ENDPOINT = os.environ.get("RDS_ENDPOINT", "")
RDS_DB_NAME = os.environ.get("RDS_DB_NAME", "enrollment")

TARGET_YEAR = 2024
TARGET_MAJOR = "computer science"

THROTTLE_CODES = {
    "ProvisionedThroughputExceededException",
    "ThrottlingException",
    "RequestLimitExceeded",
}


def _rds_engine(workers: int):
    """one pooled connection per worker, so the pool is never the bottleneck.

    max_overflow=0 keeps the pool at exactly `workers` connections: any extra
    demand queues instead of silently opening a connection outside the pool,
    which would make the measurement a lie.
    """
    password = os.environ.get("RDS_PASSWORD")
    if not password or not RDS_ENDPOINT:
        raise RuntimeError("RDS_PASSWORD and RDS_ENDPOINT must be set (see .env.example)")
    safe = urllib.parse.quote_plus(password)
    url = f"mysql+mysqlconnector://{RDS_USER}:{safe}@{RDS_ENDPOINT}/{RDS_DB_NAME}"
    return create_engine(
        url,
        connect_args={"ssl_ca": str(SSL_CA)},
        pool_size=workers,
        max_overflow=0,
        pool_pre_ping=True,
    )


def _dynamo_client(workers: int):
    """boto3 clients are thread-safe; resources are not, so this uses a client.

    the urllib3 pool defaults to 10 connections. left alone, workers above that
    would serialise on the http pool and we would be benchmarking botocore.
    """
    config = Config(
        region_name=AWS_REGION,
        max_pool_connections=max(workers, 10),
        retries={"max_attempts": 0, "mode": "standard"},
    )
    return boto3.client("dynamodb", config=config)


def _time_rds(engine) -> float:
    query = text(
        "select * from enrollment_stats "
        "where academic_year = :year and major_name = :major"
    )
    start = time.perf_counter()
    with engine.connect() as conn:
        conn.execute(query, {"year": TARGET_YEAR, "major": TARGET_MAJOR}).fetchall()
    return time.perf_counter() - start


def _time_dynamo(client) -> float:
    start = time.perf_counter()
    client.get_item(
        TableName=DYNAMO_TABLE,
        Key={
            "academic_year": {"N": str(TARGET_YEAR)},
            "major_name": {"S": TARGET_MAJOR},
        },
    )
    return time.perf_counter() - start


def run_load(name: str, call, requests: int, workers: int) -> dict:
    """fire `requests` lookups across `workers` threads and summarise the result.

    latencies are collected per request rather than dividing total elapsed time,
    because concurrency makes the average meaningless on its own: a run can post
    a healthy mean while a tenth of its requests time out.
    """
    latencies: list[float] = []
    errors: list[str] = []
    throttles = 0
    lock = threading.Lock()

    def one() -> None:
        nonlocal throttles
        try:
            elapsed = call()
        except ClientError as error:
            code = error.response["Error"]["Code"]
            with lock:
                errors.append(code)
                if code in THROTTLE_CODES:
                    throttles += 1
            return
        except Exception as error:  # pylint: disable=broad-except
            with lock:
                errors.append(type(error).__name__)
            return
        with lock:
            latencies.append(elapsed)

    print(f"\n{name}: {requests} requests across {workers} concurrent workers")
    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one) for _ in range(requests)]
        for _ in as_completed(futures):
            pass
    wall = time.perf_counter() - wall_start

    if not latencies:
        print(f"  every request failed: {sorted(set(errors))}")
        return {"backend": name, "requests": requests, "workers": workers, "errors": len(errors)}

    arr = np.array(latencies)
    summary = {
        "backend": name,
        "requests": requests,
        "workers": workers,
        "succeeded": int(arr.size),
        "errors": len(errors),
        "throttled": throttles,
        "wall_seconds": round(wall, 4),
        "throughput_rps": round(arr.size / wall, 2),
        "mean_s": round(float(arr.mean()), 4),
        "p50_s": round(float(np.percentile(arr, 50)), 4),
        "p95_s": round(float(np.percentile(arr, 95)), 4),
        "p99_s": round(float(np.percentile(arr, 99)), 4),
        "max_s": round(float(arr.max()), 4),
    }

    print(
        f"  ok {summary['succeeded']}/{requests}"
        f"  throughput {summary['throughput_rps']} req/s"
        f"  mean {summary['mean_s']}s"
        f"  p95 {summary['p95_s']}s"
        f"  p99 {summary['p99_s']}s"
    )
    if throttles:
        print(f"  throttled {throttles} times: the table's read capacity is the ceiling here")
    return summary


def warmup(call, count: int) -> None:
    """open connections before measuring, so tcp and tls handshakes are not
    charged to the first few requests."""
    for _ in range(count):
        try:
            call()
        except Exception:  # pylint: disable=broad-except
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=50, help="concurrent threads")
    parser.add_argument("--requests", type=int, default=1000, help="total lookups per backend")
    parser.add_argument("--warmup", type=int, default=10, help="unmeasured requests first")
    parser.add_argument(
        "--backend",
        choices=("rds", "dynamodb", "both"),
        default="both",
        help="which backend to load",
    )
    args = parser.parse_args()

    results = []

    if args.backend in ("dynamodb", "both"):
        client = _dynamo_client(args.workers)
        warmup(lambda: _time_dynamo(client), args.warmup)
        results.append(run_load("dynamodb", lambda: _time_dynamo(client), args.requests, args.workers))

    if args.backend in ("rds", "both"):
        engine = _rds_engine(args.workers)
        warmup(lambda: _time_rds(engine), args.warmup)
        results.append(run_load("rds", lambda: _time_rds(engine), args.requests, args.workers))
        engine.dispose()

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {RESULTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
