variable "project" {
  description = "Short name prefix for all resources"
  type        = string
  default     = "haruka"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "australiaeast"
}

variable "node_count" {
  description = "Number of AKS nodes"
  type        = number
  default     = 1

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 3
    error_message = "node_count must be between 1 and 3 (cost guardrail)."
  }
}

variable "node_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B2as_v2"
}

variable "acr_sku" {
  description = "Container Registry SKU"
  type        = string
  default     = "Basic"
}

variable "key_vault_sku" {
  description = "Key Vault SKU"
  type        = string
  default     = "standard"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    project   = "haruka-website"
    managedBy = "terraform"
  }
}

