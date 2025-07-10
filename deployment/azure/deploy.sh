#!/bin/bash

# Azure Deployment Script for Appointment Bot
set -e

# Configuration
ENVIRONMENT=${1:-prod}
RESOURCE_GROUP_NAME=${RESOURCE_GROUP_NAME:-"appointment-bot-rg"}
LOCATION=${LOCATION:-"East US"}

echo "🚀 Deploying Appointment Bot to Azure"
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Location: $LOCATION"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check required tools
for tool in az docker; do
    if ! command -v $tool &> /dev/null; then
        print_error "$tool is not installed. Please install it first."
        exit 1
    fi
done

# Check Azure login
print_info "Checking Azure authentication..."
if ! az account show > /dev/null 2>&1; then
    print_warning "Please login to Azure:"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_status "Using subscription: $SUBSCRIPTION_ID"

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP_NAME \
    --location "$LOCATION" \
    --output none

print_status "Resource group created: $RESOURCE_GROUP_NAME"

# Step 2: Generate strong password for database
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
print_info "Generated secure database password"

# Step 3: Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP_NAME \
    --template-file deployment/azure/azuredeploy.json \
    --parameters environment=$ENVIRONMENT administratorLoginPassword="$DB_PASSWORD" \
    --query 'properties.outputs' -o json)

# Extract outputs
CONTAINER_REGISTRY=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerRegistryName.value')
REGISTRY_LOGIN_SERVER=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerRegistryLoginServer.value')
POSTGRES_HOST=$(echo $DEPLOYMENT_OUTPUT | jq -r '.postgresHost.value')
REDIS_HOST=$(echo $DEPLOYMENT_OUTPUT | jq -r '.redisHost.value')
KEY_VAULT_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.keyVaultName.value')
WEB_APP_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.webAppName.value')
WEB_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.webAppUrl.value')

print_status "Infrastructure deployed successfully"

# Step 4: Get ACR credentials
echo "🔐 Getting container registry credentials..."
ACR_USERNAME=$(az acr credential show --name $CONTAINER_REGISTRY --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $CONTAINER_REGISTRY --query passwords[0].value -o tsv)

print_status "Container registry credentials retrieved"

# Step 5: Build and push Docker image
echo "🐳 Building and pushing Docker image..."

# Login to ACR
echo $ACR_PASSWORD | docker login $REGISTRY_LOGIN_SERVER --username $ACR_USERNAME --password-stdin

# Build image
docker build -t appointment-bot:latest -f Dockerfile .

# Tag image for ACR
docker tag appointment-bot:latest $REGISTRY_LOGIN_SERVER/appointment-bot:latest

# Push image
docker push $REGISTRY_LOGIN_SERVER/appointment-bot:latest

print_status "Docker image pushed to Azure Container Registry"

# Step 6: Set up Key Vault secrets
echo "🔐 Setting up Key Vault secrets..."

# Give current user access to Key Vault
CURRENT_USER=$(az account show --query user.name -o tsv)
az keyvault set-policy \
    --name $KEY_VAULT_NAME \
    --upn $CURRENT_USER \
    --secret-permissions get list set delete \
    --output none

# Store database password
az keyvault secret set \
    --vault-name $KEY_VAULT_NAME \
    --name "postgres-password" \
    --value "$DB_PASSWORD" \
    --output none

print_status "Database password stored in Key Vault"

# Prompt for API keys
echo ""
print_warning "📋 Please provide your API keys:"

# Telegram Bot Token
while true; do
    read -p "Enter your Telegram Bot Token (from @BotFather): " TELEGRAM_BOT_TOKEN
    if [[ ! -z "$TELEGRAM_BOT_TOKEN" ]]; then
        az keyvault secret set \
            --vault-name $KEY_VAULT_NAME \
            --name "telegram-bot-token" \
            --value "$TELEGRAM_BOT_TOKEN" \
            --output none
        break
    else
        print_error "Telegram Bot Token cannot be empty"
    fi
done

# OpenAI API Key
while true; do
    read -p "Enter your OpenAI API Key: " OPENAI_API_KEY
    if [[ ! -z "$OPENAI_API_KEY" ]]; then
        az keyvault secret set \
            --vault-name $KEY_VAULT_NAME \
            --name "openai-api-key" \
            --value "$OPENAI_API_KEY" \
            --output none
        break
    else
        print_error "OpenAI API Key cannot be empty"
    fi
done

# Optional: Pinecone API Key
read -p "Enter your Pinecone API Key (optional, press Enter to skip): " PINECONE_API_KEY
if [[ ! -z "$PINECONE_API_KEY" ]]; then
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "pinecone-api-key" \
        --value "$PINECONE_API_KEY" \
        --output none
    
    read -p "Enter your Pinecone Environment (e.g., us-east-1-aws): " PINECONE_ENV
    if [[ ! -z "$PINECONE_ENV" ]]; then
        az keyvault secret set \
            --vault-name $KEY_VAULT_NAME \
            --name "pinecone-environment" \
            --value "$PINECONE_ENV" \
            --output none
    fi
fi

# Optional: Neo4j credentials
read -p "Enter your Neo4j URI (optional, press Enter to skip): " NEO4J_URI
if [[ ! -z "$NEO4J_URI" ]]; then
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "neo4j-uri" \
        --value "$NEO4J_URI" \
        --output none
    
    read -p "Enter your Neo4j Password: " NEO4J_PASSWORD
    if [[ ! -z "$NEO4J_PASSWORD" ]]; then
        az keyvault secret set \
            --vault-name $KEY_VAULT_NAME \
            --name "neo4j-password" \
            --value "$NEO4J_PASSWORD" \
            --output none
    fi
fi

# Business name
read -p "Enter your Business Name: " BUSINESS_NAME
if [[ ! -z "$BUSINESS_NAME" ]]; then
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "business-name" \
        --value "$BUSINESS_NAME" \
        --output none
fi

print_status "API keys stored in Key Vault"

# Step 7: Configure Web App with Key Vault references
echo "⚙️  Configuring Web App..."

# Get Key Vault resource ID
KEY_VAULT_ID=$(az keyvault show --name $KEY_VAULT_NAME --query id -o tsv)

# Give Web App access to Key Vault
az webapp identity assign --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME --output none

# Get the Web App's managed identity
WEB_APP_PRINCIPAL_ID=$(az webapp identity show --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME --query principalId -o tsv)

# Give Web App permission to read secrets
az keyvault set-policy \
    --name $KEY_VAULT_NAME \
    --object-id $WEB_APP_PRINCIPAL_ID \
    --secret-permissions get \
    --output none

# Configure app settings with Key Vault references
az webapp config appsettings set \
    --name $WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --settings \
        "POSTGRES_PASSWORD=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=postgres-password)" \
        "TELEGRAM_BOT_TOKEN=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=telegram-bot-token)" \
        "OPENAI_API_KEY=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=openai-api-key)" \
        "PINECONE_API_KEY=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=pinecone-api-key)" \
        "PINECONE_ENVIRONMENT=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=pinecone-environment)" \
        "NEO4J_URI=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=neo4j-uri)" \
        "NEO4J_PASSWORD=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=neo4j-password)" \
        "BUSINESS_NAME=@Microsoft.KeyVault(VaultName=$KEY_VAULT_NAME;SecretName=business-name)" \
    --output none

print_status "Web App configured with Key Vault integration"

# Step 8: Restart Web App to apply changes
echo "🔄 Restarting Web App..."
az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME --output none

# Wait for startup
print_info "Waiting for application to start..."
sleep 30

# Step 9: Test deployment
echo "🧪 Testing deployment..."

# Health check
HEALTH_RESPONSE=$(curl -s "$WEB_APP_URL/health" || echo "Health check failed")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_status "Health check passed"
else
    print_warning "Health check may have issues: $HEALTH_RESPONSE"
fi

# Step 10: Set up Telegram webhook
echo "🤖 Setting up Telegram webhook..."
if [[ ! -z "$TELEGRAM_BOT_TOKEN" ]]; then
    WEBHOOK_SECRET=$(openssl rand -hex 32)
    
    # Store webhook secret
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "telegram-webhook-secret" \
        --value "$WEBHOOK_SECRET" \
        --output none
    
    # Set webhook URL
    WEBHOOK_URL="$WEB_APP_URL/webhook/$WEBHOOK_SECRET"
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$WEBHOOK_URL\"}" \
        > /dev/null 2>&1
    
    print_status "Telegram webhook configured"
else
    print_warning "Telegram webhook not configured (no bot token provided)"
fi

# Step 11: Initialize database
echo "🗄️  Initializing database..."
curl -X POST "$WEB_APP_URL/debug/reset-database" > /dev/null 2>&1 || print_warning "Database initialization may have failed"

print_status "Database initialization attempted"

# Summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Location: $LOCATION"
echo ""
echo "🌐 Service URLs:"
echo "Web App: $WEB_APP_URL"
echo "Health Check: $WEB_APP_URL/health"
echo "API Docs: $WEB_APP_URL/docs"
echo ""
echo "🗄️  Database Info:"
echo "PostgreSQL Host: $POSTGRES_HOST"
echo "Redis Host: $REDIS_HOST"
echo ""
echo "🔐 Security:"
echo "Key Vault: $KEY_VAULT_NAME"
echo "Container Registry: $REGISTRY_LOGIN_SERVER"
echo ""
echo "📋 Next Steps:"
echo "1. Test the health endpoint: curl $WEB_APP_URL/health"
echo "2. Upload knowledge base documents via API"
echo "3. Test the Telegram bot"
echo "4. Monitor logs in Azure Portal"
echo ""
echo "🔧 Useful Commands:"
echo "View logs: az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME"
echo "Restart app: az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME"
echo "Scale app: az webapp up --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME --sku B2"

print_status "Azure deployment completed!"

# Optional: Open Azure Portal
echo ""
read -p "Would you like to open the Azure Portal to view your resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://portal.azure.com/#@/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/overview"
fi

echo ""
print_status "All done! Your Telegram bot is live at: $WEB_APP_URL 🚀"