# Provider configuration
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}


provider "azurerm" {
  features {} #
  subscription_id = "4934371f-642a-41f0-98a1-80a92930af2f"

}