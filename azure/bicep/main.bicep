@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Name of the Container App Environment')
param containerAppEnvironmentName string = 'appointment-bot-env'

@description('Name of the Container App')
param containerAppName string = 'appointment-bot'

@description('Name of the Container Registry')
param containerRegistryName string = 'appointmentbotacr'

@description('Name of the PostgreSQL server')
param postgresServerName string = 'appointment-postgres'

@description('Name of the Key Vault')
param keyVaultName string = 'appointment-kv'

@description('Name of the Log Analytics workspace')
param logAnalyticsWorkspaceName string = 'appointment-logs'

@description('Name of the Application Insights')
param appInsightsName string = 'appointment-insights'

@description('Name of the Redis cache')
param redisCacheName string = 'appointment-redis'

@description('Administrator username for PostgreSQL')
@secure()
param postgresAdminUsername string

@description('Administrator password for PostgreSQL')
@secure()
param postgresAdminPassword string

@description('Telegram Bot Token')
@secure()
param telegramBotToken string

@description('OpenAI API Key')
@secure()
param openaiApiKey string

@description('Neo4j connection details')
@secure()
param neo4jUri string

@description('Neo4j username')
@secure()
param neo4jUsername string

@description('Neo4j password')
@secure()
param neo4jPassword string

@description('Pinecone API Key')
@secure()
param pineconeApiKey string

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'pergb2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-09-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2021-11-01-preview' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enableRbacAuthorization: true
  }
}

// PostgreSQL Flexible Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '13'
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: null
      privateDnsZoneArmResourceId: null
      publicNetworkAccess: 'Enabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    maintenanceWindow: {
      customWindow: 'Disabled'
      dayOfWeek: 0
      startHour: 0
      startMinute: 0
    }
  }
}

// PostgreSQL Database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2021-06-01' = {
  parent: postgresServer
  name: 'appointment_db'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.UTF8'
  }
}

// PostgreSQL Firewall Rule (Allow all Azure services)
resource postgresFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2021-06-01' = {
  parent: postgresServer
  name: 'AllowAllAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Redis Cache
resource redisCache 'Microsoft.Cache/redis@2021-06-01' = {
  name: redisCacheName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

// Container App Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: containerAppEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Key Vault Secrets
resource postgresHostSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'postgres-host'
  properties: {
    value: postgresServer.properties.fullyQualifiedDomainName
  }
}

resource postgresUserSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'postgres-user'
  properties: {
    value: postgresAdminUsername
  }
}

resource postgresPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'postgres-password'
  properties: {
    value: postgresAdminPassword
  }
}

resource postgresDbSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'postgres-db'
  properties: {
    value: 'appointment_db'
  }
}

resource redisUrlSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'redis-url'
  properties: {
    value: 'redis://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}?ssl=true'
  }
}

resource telegramBotTokenSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'telegram-bot-token'
  properties: {
    value: telegramBotToken
  }
}

resource openaiApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openaiApiKey
  }
}

resource neo4jUriSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'neo4j-uri'
  properties: {
    value: neo4jUri
  }
}

resource neo4jUsernameSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'neo4j-username'
  properties: {
    value: neo4jUsername
  }
}

resource neo4jPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'neo4j-password'
  properties: {
    value: neo4jPassword
  }
}

resource pineconeApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-11-01-preview' = {
  parent: keyVault
  name: 'pinecone-api-key'
  properties: {
    value: pineconeApiKey
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: [
        {
          name: 'postgres-host'
          keyVaultUrl: postgresHostSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'postgres-user'
          keyVaultUrl: postgresUserSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'postgres-password'
          keyVaultUrl: postgresPasswordSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'postgres-db'
          keyVaultUrl: postgresDbSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'redis-url'
          keyVaultUrl: redisUrlSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'telegram-bot-token'
          keyVaultUrl: telegramBotTokenSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'openai-api-key'
          keyVaultUrl: openaiApiKeySecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'neo4j-uri'
          keyVaultUrl: neo4jUriSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'neo4j-username'
          keyVaultUrl: neo4jUsernameSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'neo4j-password'
          keyVaultUrl: neo4jPasswordSecret.properties.secretUri
          identity: 'system'
        }
        {
          name: 'pinecone-api-key'
          keyVaultUrl: pineconeApiKeySecret.properties.secretUri
          identity: 'system'
        }
      ]
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.properties.adminUserEnabled ? containerRegistry.name : null
          passwordSecretRef: containerRegistry.properties.adminUserEnabled ? 'registry-password' : null
        }
      ]
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'appointment-bot'
          image: '${containerRegistry.properties.loginServer}/appointment-bot:latest'
          env: [
            {
              name: 'POSTGRES_HOST'
              secretRef: 'postgres-host'
            }
            {
              name: 'POSTGRES_USER'
              secretRef: 'postgres-user'
            }
            {
              name: 'POSTGRES_PASSWORD'
              secretRef: 'postgres-password'
            }
            {
              name: 'POSTGRES_DB'
              secretRef: 'postgres-db'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'TELEGRAM_BOT_TOKEN'
              secretRef: 'telegram-bot-token'
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'NEO4J_URI'
              secretRef: 'neo4j-uri'
            }
            {
              name: 'NEO4J_USERNAME'
              secretRef: 'neo4j-username'
            }
            {
              name: 'NEO4J_PASSWORD'
              secretRef: 'neo4j-password'
            }
            {
              name: 'PINECONE_API_KEY'
              secretRef: 'pinecone-api-key'
            }
            {
              name: 'VECTOR_DB_PROVIDER'
              value: 'pinecone'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

// Role Assignment for Container App to access Key Vault
resource keyVaultAccessPolicy 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(keyVault.id, containerApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output postgresServerName string = postgresServer.properties.fullyQualifiedDomainName
output keyVaultName string = keyVault.name