# -- Identity & naming ------------------------------                                 

data "azurerm_client_config" "current" {}

locals {
  rg_name  = "rg-${var.project}"
  acr_name = "acr${var.project}" # alphanumeric only
  kv_name  = "kv-${var.project}" # <= 24 chars
  aks_name = "aks-${var.project}"
}

# -- Resource group ------------------------------ 

resource "azurerm_resource_group" "main" {
  name     = local.rg_name
  location = var.location
  tags     = var.tags
}

# -- Container registry ------------------------------  

resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = false
  tags                = var.tags
}

# -- AKS cluter ------------------------------

resource "azurerm_kubernetes_cluster" "main" {
  name                = local.aks_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  dns_prefix          = local.aks_name

  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.node_vm_size

    upgrade_settings {
      max_surge = "10%"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }

  tags = var.tags
}

# -- Let AKS nodes pull images from ACR  ------------------------------ 

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                            = azurerm_container_registry.main.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}

# -- Key vault ------------------------------ 

resource "azurerm_key_vault" "main" {
  name                       = local.kv_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = var.key_vault_sku
  rbac_authorization_enabled = true
  tags                       = var.tags
}

# Let you (operator) seed secrets via `az keyvault secret set`
resource "azurerm_role_assignment" "operator_kv_officer" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# -- Backend pod identity ------------------------------ 

resource "azurerm_user_assigned_identity" "backend" {
  name                = "id-${var.project}-backend"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}

# Trust: K8s ServiceAccount "haruka/backend" -> this UAMI, via AKS OIDC issuer
resource "azurerm_federated_identity_credential" "backend" {
  name                      = "backend-federated-credential"
  user_assigned_identity_id = azurerm_user_assigned_identity.backend.id
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject                   = "system:serviceaccount:haruka:backend"
}

# Let the UAMI read secrets from Key Vault"
resource "azurerm_role_assignment" "backend_kv_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

# -- Static public IP for the nginx ingress ------------------------------ 

resource "azurerm_public_ip" "ingress" {
  name                = "pip-${var.project}-ingress"
  resource_group_name = azurerm_kubernetes_cluster.main.node_resource_group
  location            = azurerm_resource_group.main.location
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

# -- CI/CD identity (GitHub Actions) ------------------------------ 

resource "azurerm_user_assigned_identity" "cicd" {
  name                = "id-${var.project}-cicd"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags
}

# Trust: GitHub Actions on the deploy branch -> this UAMI, via GitHub's OIDC issuer
resource "azurerm_federated_identity_credential" "cicd" {
  name                      = "github-actions-deploy"
  user_assigned_identity_id = azurerm_user_assigned_identity.cicd.id
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = "https://token.actions.githubusercontent.com"
  subject                   = "repo:${var.github_repo}:ref:refs/heads/${var.github_branch}"
}

# Let CI run `az acr build` (queues an ACR Task -> needs Contributor, not just AcrPush)
resource "azurerm_role_assignment" "cicd_acr" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.cicd.principal_id
}

# Let CI run `az aks get-credentials` and kubectl apply
resource "azurerm_role_assignment" "cicd_aks" {
  scope                = azurerm_kubernetes_cluster.main.id
  role_definition_name = "Azure Kubernetes Service Cluster User Role"
  principal_id         = azurerm_user_assigned_identity.cicd.principal_id
}

