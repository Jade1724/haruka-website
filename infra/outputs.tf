output "ingress_ip" {
  description = "Static public IP for the nginx ingress"
  value       = azurerm_public_ip.ingress.ip_address
}

output "acr_login_server" {
  description = "ACR hostname for docker push/pull"
  value       = azurerm_container_registry.main.login_server
}

output "key_vault_name" {
  description = "Key Vault name for `az keyvault secrest set`"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "Key Vault URI for the SecretProviderClass"
  value       = azurerm_key_vault.main.vault_uri
}

output "uami_client_id" {
  description = "Backend UAMI client ID for the ServiceAccount annotation"
  value       = azurerm_user_assigned_identity.backend.client_id
}

output "tenant_id" {
  description = "Tenant ID for the SecretProviderClass"
  value       = data.azurerm_client_config.current.tenant_id
}

output "node_resource_group" {
  description = "AKS-managed RG holding the load balancer and node IP"
  value       = azurerm_kubernetes_cluster.main.node_resource_group
}

