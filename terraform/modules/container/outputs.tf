output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "acr_name" {
  value = azurerm_container_registry.main.name
}

output "container_app_fqdn" {
  value = azurerm_container_app.streamlit.latest_revision_fqdn
}
