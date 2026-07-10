/**
 * provisions the two backends this practicum compares:
 *
 *   - an instance-based amazon rds (mysql) database, billed per hour
 *   - a serverless dynamodb table, billed per request
 *
 * both live in the account's default vpc so the benchmark can run from a
 * laptop without standing up networking. tear everything down with
 * `terraform destroy` once the numbers are collected.
 */

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# --- rds: instance-based, always on ---

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds"
  description = "mysql access for the benchmark client"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "mysql" {
  for_each = toset(var.allowed_cidr_blocks)

  security_group_id = aws_security_group.rds.id
  description       = "mysql from the benchmark client"
  cidr_ipv4         = each.value
  from_port         = 3306
  to_port           = 3306
  ip_protocol       = "tcp"
}

resource "aws_db_instance" "this" {
  identifier     = var.project_name
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true
  multi_az               = var.multi_az

  # this is a throwaway benchmark instance: no backups to pay for, no snapshot
  # on the way out, and no deletion guard blocking `terraform destroy`.
  backup_retention_period = 0
  skip_final_snapshot     = true
  deletion_protection     = false
  apply_immediately       = true
}

# --- dynamodb: serverless, billed per request ---

resource "aws_dynamodb_table" "this" {
  name         = var.dynamodb_table_name
  billing_mode = var.dynamodb_billing_mode

  # the access pattern is "give me one major for one year", so the composite key
  # answers it with a single get_item and no secondary index.
  hash_key  = "academic_year"
  range_key = "major_name"

  read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
  write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null

  attribute {
    name = "academic_year"
    type = "N"
  }

  attribute {
    name = "major_name"
    type = "S"
  }
}
