#!/bin/bash

set -e

# Configuration
RESOURCE_GROUP="appointment-bot-rg"
LOCATION="Central India"
CONTAINER_REGISTRY="appointmentbotacr"
IMAGE_NAME="appointment-bot"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Azure deployment for Appointment Bot${NC}"

# Check if logged in to Azure
if ! az account show >/dev/null 2>&1; then
    echo -e "${RED}Error: Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Create resource group
echo -e "${YELLOW}Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location "$LOCATION"

# Deploy infrastructure using Bicep
echo -e "${YELLOW}Deploying infrastructure...${NC}"
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file azure/bicep/main.bicep \
    --parameters @azure/bicep/parameters.json \
    --verbose

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push Docker image
echo -e "${YELLOW}Building and pushing Docker image...${NC}"
az acr build --registry $CONTAINER_REGISTRY --image $IMAGE_NAME:$IMAGE_TAG --file Dockerfile.azure .

# Update Container App with new image
echo -e "${YELLOW}Updating Container App...${NC}"
az containerapp update \
    --name appointment-bot \
    --resource-group $RESOURCE_GROUP \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

# Get application URL
APP_URL=$(az containerapp show --name appointment-bot --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Application URL: https://$APP_URL${NC}"
echo -e "${GREEN}Health check: https://$APP_URL/health${NC}"
echo -e "${GREEN}API docs: https://$APP_URL/docs${NC}"

# Test the deployment
echo -e "${YELLOW}Testing deployment...${NC}"
if curl -f https://$APP_URL/health >/dev/null 2>&1; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed. Please check the logs.${NC}"
    echo "To check logs run: az containerapp logs show --name appointment-bot --resource-group $RESOURCE_GROUP --follow"
fi