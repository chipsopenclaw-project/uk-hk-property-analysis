# ── Azure Data Factory ─────────────────────────────────────
resource "azurerm_data_factory" "main" {
  name                = "adf-${var.project}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# ── Grant ADF Managed Identity access to ADLS ─────────────
resource "azurerm_role_assignment" "adf_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}

# ── Grant ADF Managed Identity access to Key Vault ────────
resource "azurerm_key_vault_access_policy" "adf" {
  key_vault_id = var.key_vault_id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_data_factory.main.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

# ── Linked Service: ADLS Gen2 ──────────────────────────────
resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "adls" {
  name                 = "ls_adls_${var.environment}"
  data_factory_id      = azurerm_data_factory.main.id
  url                  = "https://${var.storage_account_name}.dfs.core.windows.net"
  use_managed_identity = true
}

# ── Linked Service: HTTP (Land Registry) ──────────────────
resource "azurerm_data_factory_linked_service_web" "land_registry" {
  name                = "ls_http_land_registry"
  data_factory_id     = azurerm_data_factory.main.id
  url                 = "https://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com"
  authentication_type = "Anonymous"
}

# ── Dataset: HTTP Source (Land Registry) ──────────────────
resource "azurerm_data_factory_dataset_http" "land_registry_csv" {
  name                = "ds_http_land_registry_csv"
  data_factory_id     = azurerm_data_factory.main.id
  linked_service_name = azurerm_data_factory_linked_service_web.land_registry.name
  relative_url        = "@dataset().relative_url"
  request_method      = "GET"

  parameters = {
    relative_url = ""
  }
}

# ── Dataset: ADLS Bronze Destination ──────────────────────
resource "azurerm_data_factory_dataset_azure_blob" "bronze_land_registry" {
  name                = "ds_adls_bronze_land_registry"
  data_factory_id     = azurerm_data_factory.main.id
  linked_service_name = azurerm_data_factory_linked_service_data_lake_storage_gen2.adls.name
  path                = "land-registry"
  filename            = "@dataset().filename"

  parameters = {
    folder   = ""
    filename = ""
  }
}

data "azurerm_client_config" "current" {}
