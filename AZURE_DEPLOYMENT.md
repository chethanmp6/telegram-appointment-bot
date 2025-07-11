# Azure Cloud Deployment Guide

## Overview
This guide provides step-by-step instructions to deploy the Telegram Appointment Bot to Azure Cloud using Container Apps, PostgreSQL, Redis, and Neo4j AuraDB.

## Prerequisites
- Azure CLI installed and configured
- Docker installed
- Azure subscription with appropriate permissions
- Neo4j AuraDB account
- API keys for OpenAI/Anthropic, Telegram, and Pinecone

## Architecture on Azure

### Services Used
- **Azure Container Apps**: Serverless container hosting
- **Azure Database for PostgreSQL**: Managed PostgreSQL service
- **Azure Cache for Redis**: In-memory caching
- **Azure Container Registry**: Container image storage
- **Azure Key Vault**: Secrets management
- **Azure Monitor**: Logging and monitoring
- **Neo4j AuraDB**: Managed graph database (external)

## Step-by-Step Deployment

### 1. Prerequisites Setup

#### Install Azure CLI
```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### Login to Azure
```bash
az login
az account set --subscription "your-subscription-id"
```

### 2. Set Up Neo4j AuraDB

1. **Create Neo4j AuraDB Instance**
   - Visit [Neo4j AuraDB Console](https://console.neo4j.io)
   - Create new database: `appointment-bot-graph`
   - Choose region closest to Azure region
   - Note connection details (URI, username, password)

2. **Configure Connection**
   - Update `azure/bicep/parameters.json` with Neo4j details
   - Ensure firewall allows Azure Container Apps access

### 3. Configure API Keys

#### Update Parameters File
Edit `azure/bicep/parameters.json`:
```json
{
  "telegramBotToken": {
    "value": "YOUR_TELEGRAM_BOT_TOKEN"
  },
  "openaiApiKey": {
    "value": "YOUR_OPENAI_API_KEY"
  },
  "neo4jUri": {
    "value": "neo4j+s://your-database-id.databases.neo4j.io"
  },
  "neo4jUsername": {
    "value": "neo4j"
  },
  "neo4jPassword": {
    "value": "your-neo4j-password"
  },
  "pineconeApiKey": {
    "value": "YOUR_PINECONE_API_KEY"
  }
}
```

### 4. Deploy Infrastructure

#### Option A: Automated Deployment
```bash
# Make script executable
chmod +x azure/deploy.sh

# Run deployment
./azure/deploy.sh
```

#### Option B: Manual Deployment
```bash
# Create resource group
az group create --name appointment-bot-rg --location "East US"

# Deploy infrastructure
az deployment group create \
    --resource-group appointment-bot-rg \
    --template-file azure/bicep/main.bicep \
    --parameters @azure/bicep/parameters.json

# Build and push image
az acr build --registry appointmentbotacr --image appointment-bot:latest --file Dockerfile.azure .
```

### 5. Configure Telegram Webhook

After deployment, configure your Telegram bot webhook:
```bash
# Get your Container App URL
APP_URL=$(az containerapp show --name appointment-bot --resource-group appointment-bot-rg --query properties.configuration.ingress.fqdn --output tsv)

# Set webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://$APP_URL/api/v1/telegram/webhook\"}"
```

### 6. Initialize Databases

```bash
# Initialize PostgreSQL tables
curl -X POST https://$APP_URL/api/v1/database/init

# Initialize Neo4j schema
curl -X POST https://$APP_URL/api/v1/graph/init

# Initialize vector database
curl -X POST https://$APP_URL/api/v1/knowledge/init
```

### 7. Verify Deployment

```bash
# Health check
curl https://$APP_URL/health

# Test API
curl https://$APP_URL/docs
```

## Configuration Details

### Environment Variables
The application uses these environment variables (managed via Azure Key Vault):
- `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- `REDIS_URL`
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `VECTOR_DB_PROVIDER`

### Resource Sizing
- **Container App**: 0.5 CPU, 1Gi memory (scales 1-3 instances)
- **PostgreSQL**: Standard_B1ms (1 vCore, 2GB RAM)
- **Redis**: Basic C0 (250MB)

## Monitoring and Logs

### View Logs
```bash
# Real-time logs
az containerapp logs show --name appointment-bot --resource-group appointment-bot-rg --follow

# Application Insights
az monitor app-insights component show --app appointment-insights --resource-group appointment-bot-rg
```

### Health Endpoints
- `/health` - Overall system health
- `/api/v1/graph/health` - Neo4j connectivity
- `/api/v1/knowledge/health` - Vector database status

## Scaling Configuration

### Auto-scaling Rules
- HTTP requests: Scale up at 100 concurrent requests
- Min replicas: 1
- Max replicas: 3

### Manual Scaling
```bash
az containerapp revision set-active \
    --name appointment-bot \
    --resource-group appointment-bot-rg \
    --revision-name appointment-bot--revision-suffix
```

## Security Features

### Key Vault Integration
- All secrets stored in Azure Key Vault
- System-assigned managed identity for access
- RBAC permissions for Container App

### Network Security
- HTTPS-only ingress
- Container Apps environment isolation
- Database firewall rules

## Backup and Recovery

### PostgreSQL Backup
- Automated daily backups (7-day retention)
- Point-in-time recovery available

### Neo4j Backup
- AuraDB automatic backups
- Contact Neo4j support for restore

## Cost Optimization

### Resource Tiers
- **Development**: Use Basic/Free tiers
- **Production**: Upgrade to Standard/Premium for SLA

### Estimated Monthly Costs
- Container Apps: $10-30
- PostgreSQL: $15-50
- Redis: $5-15
- Neo4j AuraDB: $0-65 (depending on tier)
- Total: $30-160/month

## Troubleshooting

### Common Issues

1. **Container App won't start**
   ```bash
   # Check logs
   az containerapp logs show --name appointment-bot --resource-group appointment-bot-rg --tail 50
   ```

2. **Database connection errors**
   ```bash
   # Verify PostgreSQL firewall
   az postgres flexible-server firewall-rule list --name appointment-postgres --resource-group appointment-bot-rg
   ```

3. **Telegram webhook not working**
   ```bash
   # Check webhook status
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

### Debug Commands
```bash
# Container App details
az containerapp show --name appointment-bot --resource-group appointment-bot-rg

# Key Vault access
az keyvault secret list --vault-name appointment-kv

# PostgreSQL connection test
az postgres flexible-server connect --name appointment-postgres --username appointmentadmin
```

## Updates and Maintenance

### Application Updates
```bash
# Build new image
az acr build --registry appointmentbotacr --image appointment-bot:v2 .

# Update Container App
az containerapp update \
    --name appointment-bot \
    --resource-group appointment-bot-rg \
    --image appointmentbotacr.azurecr.io/appointment-bot:v2
```

### Infrastructure Updates
```bash
# Update using Bicep
az deployment group create \
    --resource-group appointment-bot-rg \
    --template-file azure/bicep/main.bicep \
    --parameters @azure/bicep/parameters.json
```

## Production Checklist

- [ ] Configure production API keys
- [ ] Set up Neo4j AuraDB with appropriate tier
- [ ] Configure Telegram webhook with HTTPS
- [ ] Set up monitoring alerts
- [ ] Configure backup retention policies
- [ ] Review security settings
- [ ] Test all endpoints
- [ ] Set up CI/CD pipeline (optional)

## Support and Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Neo4j AuraDB Documentation](https://neo4j.com/docs/aura/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)

For issues, check logs first, then consult the troubleshooting section above.