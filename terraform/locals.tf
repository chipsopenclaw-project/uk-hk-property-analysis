locals {
  common_tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
    repo        = "uk-hk-property-analysis"
  }
}
