# ── Azure Container Registry ───────────────────────────────
resource "azurerm_container_registry" "main" {
  name                = "acr${var.project}${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = var.tags
}

# ── Log Analytics Workspace (required by Container Apps) ───
resource "azurerm_log_analytics_workspace" "container" {
  name                = "log-${var.project}-container-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

# ── Container Apps Environment ─────────────────────────────
resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project}-${var.environment}"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.container.id

  tags = var.tags
}

# ── Container App (Streamlit) ──────────────────────────────
resource "azurerm_container_app" "streamlit" {
  name                         = "ca-${var.project}-streamlit-${var.environment}"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  template {
    container {
      name   = "streamlit"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.5
      memory = "1Gi"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}
