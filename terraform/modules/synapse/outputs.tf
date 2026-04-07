output "workspace_name" {
  value = azurerm_synapse_workspace.main.name
}

output "workspace_id" {
  value = azurerm_synapse_workspace.main.id
}

output "synapse_principal_id" {
  value = azurerm_synapse_workspace.main.identity[0].principal_id
}
