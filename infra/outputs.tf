output "rds_endpoint" {
  description = "host:port of the mysql instance. strip the port for RDS_ENDPOINT in .env"
  value       = aws_db_instance.this.endpoint
}

output "rds_address" {
  description = "hostname only, ready to paste into RDS_ENDPOINT"
  value       = aws_db_instance.this.address
}

output "rds_multi_az" {
  description = "whether the instance is replicated across availability zones"
  value       = aws_db_instance.this.multi_az
}

output "dynamodb_table_name" {
  description = "table name, ready to paste into DYNAMO_TABLE"
  value       = aws_dynamodb_table.this.name
}

output "dynamodb_billing_mode" {
  description = "billing model in force for the table"
  value       = aws_dynamodb_table.this.billing_mode
}

output "env_file_snippet" {
  description = "paste this into .env once the apply finishes"
  value       = <<-EOT
    AWS_REGION=${var.aws_region}
    DYNAMO_TABLE=${aws_dynamodb_table.this.name}
    RDS_USER=${var.db_username}
    RDS_ENDPOINT=${aws_db_instance.this.address}
    RDS_DB_NAME=${var.db_name}
  EOT
}
