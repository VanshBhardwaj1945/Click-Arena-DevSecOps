output "game_url" {
  value       = "https://${azurerm_container_app.main.ingress[0].fqdn}"
  description = "Public URL of the live game"
}

output "acr_login_server" {
  value       = azurerm_container_registry.mainACR.login_server
  description = "ACR login server for pushing images"
}