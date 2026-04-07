# ── Random password for Synapse SQL admin ──────────────────
resource "random_password" "synapse_sql" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# ── Synapse Workspace ──────────────────────────────────────
resource "azurerm_synapse_workspace" "main" {
  name                                 = "syn-${var.project}-${var.environment}"
  resource_group_name                  = var.resource_group_name
  location                             = var.location
  storage_data_lake_gen2_filesystem_id = var.adls_filesystem_id
  sql_administrator_login              = "sqladmin"
  sql_administrator_login_password     = random_password.synapse_sql.result

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# ── Store SQL password in Key Vault ───────────────────────
resource "azurerm_key_vault_secret" "synapse_sql_password" {
  name         = "synapse-sql-admin-password"
  value        = random_password.synapse_sql.result
  key_vault_id = var.key_vault_id
}

# ── Synapse Spark Pool ─────────────────────────────────────
resource "azurerm_synapse_spark_pool" "main" {
  name                 = "sparkpool${var.environment}"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  node_size_family     = "MemoryOptimized"
  node_size            = var.spark_node_size
  spark_version        = "3.4"

  auto_pause {
    delay_in_minutes = 15
  }

  auto_scale {
    min_node_count = var.spark_min_node_count
    max_node_count = var.spark_max_node_count
  }

  tags = var.tags
}

# ── Grant Synapse Managed Identity access to ADLS ─────────
resource "azurerm_role_assignment" "synapse_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.main.identity[0].principal_id
}

# ── Synapse Firewall: allow Azure services ─────────────────
resource "azurerm_synapse_firewall_rule" "allow_azure" {
  name                 = "AllowAllWindowsAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}
