variable "resource_group_name"  { type = string }
variable "location"             { type = string }
variable "project"              { type = string }
variable "environment"          { type = string }
variable "storage_account_name" { type = string }
variable "storage_account_id"   { type = string }
variable "adls_filesystem_id"   { type = string }
variable "key_vault_id"         { type = string }

variable "spark_node_size" {
  type    = string
  default = "Small"
}

variable "spark_min_node_count" {
  type    = number
  default = 3
}

variable "spark_max_node_count" {
  type    = number
  default = 5
}

variable "tags" { type = map(string) }
