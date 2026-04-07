output "storage_account_name" {
  value = azurerm_storage_account.adls.name
}

output "storage_account_id" {
  value = azurerm_storage_account.adls.id
}

output "adls_gold_filesystem_id" {
  value = azurerm_storage_data_lake_gen2_filesystem.gold.id
}

output "primary_dfs_endpoint" {
  value = azurerm_storage_account.adls.primary_dfs_endpoint
}
