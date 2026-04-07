output "resource_group_name" {
  description = "Main resource group name"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "ADLS Gen2 storage account name"
  value       = module.storage.storage_account_name
}

output "adf_name" {
  description = "Azure Data Factory name"
  value       = module.adf.adf_name
}

output "synapse_workspace_name" {
  description = "Synapse Analytics workspace name"
  value       = module.synapse.workspace_name
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.keyvault.key_vault_name
}

output "acr_login_server" {
  description = "Container Registry login server"
  value       = module.container.acr_login_server
}

output "container_app_fqdn" {
  description = "Streamlit Container App public URL"
  value       = module.container.container_app_fqdn
}
