"""create the dynamodb table used for the enrollment archive.

single-table design: partition key = academic_year, sort key = major_name,
which serves the "give me all majors for year X" access pattern without joins.
"""

import os

import boto3

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "au_enrollment_stats")

dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)


def create_table() -> None:
    try:
        dynamodb.create_table(
            TableName=DYNAMO_TABLE,
            KeySchema=[
                {"AttributeName": "academic_year", "KeyType": "HASH"},  # partition key
                {"AttributeName": "major_name", "KeyType": "RANGE"},  # sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "academic_year", "AttributeType": "N"},
                {"AttributeName": "major_name", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        print("dynamodb table creation initiated successfully")
    except Exception as error:  # pylint: disable=broad-except
        print(f"error creating table: {error}")


if __name__ == "__main__":
    create_table()
