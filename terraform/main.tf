resource "azurerm_resource_group" "mainRG" {
  name     = "click-arena-rg"
  location = "East Us"
}


resource "azurerm_container_registry" "mainACR" {
  name                = "clickarenaregistry"
  resource_group_name = azurerm_resource_group.mainRG.name
  location            = azurerm_resource_group.mainRG.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_log_analytics_workspace" "mainLA" {
  name                = "click-arena-logs"
  location            = azurerm_resource_group.mainRG.location
  resource_group_name = azurerm_resource_group.mainRG.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "mainCAE" {
  name                       = "click-arena-env"
  location                   = azurerm_resource_group.mainRG.location
  resource_group_name        = azurerm_resource_group.mainRG.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.mainLA.id
}

resource "azurerm_container_app" "main" {
  name                         = "click-arena"
  container_app_environment_id = azurerm_container_app_environment.mainCAE.id
  resource_group_name          = azurerm_resource_group.mainRG.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.mainACR.login_server
    username             = azurerm_container_registry.mainACR.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.mainACR.admin_password
  }

  template {
    container {
      name   = "click-arena"
      image  = "${azurerm_container_registry.mainACR.login_server}/click-arena:v3"
      cpu    = 0.5
      memory = "1Gi"
    }

    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    external_enabled = true
    target_port      = 5000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}