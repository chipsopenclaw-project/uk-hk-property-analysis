variable "project" {
  description = "Project short name used in all resource names"
  type        = string
  default     = "ukhkprop"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "uksouth"
}
