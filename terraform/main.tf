terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-ukhkprop-tfstate"
    storage_account_name = "stukhkproptfstate"
    container_name       = "tfstate"
    key                  = "dev/terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}

# ── Data Sources ───────────────────────────────────────────
data "azurerm_client_config" "current" {}

# ── Resource Group ─────────────────────────────────────────
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project}-${var.environment}"
  location = var.location
  tags     = local.common_tags
}

module "storage" {
  source              = "./modules/storage"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project             = var.project
  environment         = var.environment
  tags                = local.common_tags
}

module "keyvault" {
  source              = "./modules/keyvault"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project             = var.project
  environment         = var.environment
  tenant_id           = data.azurerm_client_config.current.tenant_id
  object_id           = data.azurerm_client_config.current.object_id
  tags                = local.common_tags
}

module "adf" {
  source               = "./modules/adf"
  resource_group_name  = azurerm_resource_group.main.name
  location             = var.location
  project              = var.project
  environment          = var.environment
  storage_account_name = module.storage.storage_account_name
  storage_account_id   = module.storage.storage_account_id
  key_vault_id         = module.keyvault.key_vault_id
  tags                 = local.common_tags
}

module "synapse" {
  source               = "./modules/synapse"
  resource_group_name  = azurerm_resource_group.main.name
  location             = var.location
  project              = var.project
  environment          = var.environment
  storage_account_name = module.storage.storage_account_name
  storage_account_id   = module.storage.storage_account_id
  adls_filesystem_id   = module.storage.adls_gold_filesystem_id
  key_vault_id         = module.keyvault.key_vault_id
  spark_node_size      = "Small"
  spark_min_node_count = 3
  spark_max_node_count = 5
  tags                 = local.common_tags
}

module "container" {
  source              = "./modules/container"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project             = var.project
  environment         = var.environment
  tags                = local.common_tags
}

module "monitoring" {
  source              = "./modules/monitoring"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  project             = var.project
  environment         = var.environment
  tags                = local.common_tags
}
