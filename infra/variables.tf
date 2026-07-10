variable "aws_region" {
  description = "region both backends are provisioned in"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "prefix applied to resource names and tags"
  type        = string
  default     = "rds-vs-dynamodb-practicum"
}

# --- rds ---

variable "db_name" {
  description = "initial mysql schema created on the instance"
  type        = string
  default     = "enrollment"
}

variable "db_username" {
  description = "mysql master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "mysql master password. supply via TF_VAR_db_password, never in a committed file"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "rds instance size. db.t3.micro is free-tier eligible"
  type        = string
  default     = "db.t3.micro"
}

variable "multi_az" {
  description = <<-EOT
    deploy rds across two availability zones. doubles the instance cost, so it is
    off by default. dynamodb replicates across azs regardless of this setting.
  EOT
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = <<-EOT
    cidr ranges permitted to reach mysql on port 3306. no default on purpose:
    the benchmark runs from a laptop, so this must be your own public ip as a /32.
    never widen this to 0.0.0.0/0.
  EOT
  type        = list(string)

  validation {
    condition     = !contains(var.allowed_cidr_blocks, "0.0.0.0/0")
    error_message = "0.0.0.0/0 exposes the database to the public internet. supply your own /32."
  }
}

# --- dynamodb ---

variable "dynamodb_table_name" {
  description = "single-table name for the enrollment archive"
  type        = string
  default     = "au_enrollment_stats"
}

variable "dynamodb_billing_mode" {
  description = <<-EOT
    PAY_PER_REQUEST matches the cost argument this practicum makes: you pay per
    query and effectively nothing while idle. PROVISIONED is offered so the two
    billing models can be compared under concurrent load, where a low read
    capacity will throttle.
  EOT
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.dynamodb_billing_mode)
    error_message = "dynamodb_billing_mode must be PAY_PER_REQUEST or PROVISIONED."
  }
}

variable "dynamodb_read_capacity" {
  description = "read capacity units. ignored unless dynamodb_billing_mode is PROVISIONED"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "write capacity units. ignored unless dynamodb_billing_mode is PROVISIONED"
  type        = number
  default     = 5
}
