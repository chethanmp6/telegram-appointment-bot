#!/bin/bash

set -e

# Configuration
RESOURCE_GROUP="appointment-bot-rg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This will delete all Azure resources for the Appointment Bot.${NC}"
echo -e "${RED}This action cannot be undone!${NC}"
echo -e "${YELLOW}Resource Group: $RESOURCE_GROUP${NC}"

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Cleanup cancelled.${NC}"
    exit 0
fi

# Check if logged in to Azure
if ! az account show >/dev/null 2>&1; then
    echo -e "${RED}Error: Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP >/dev/null 2>&1; then
    echo -e "${YELLOW}Resource group $RESOURCE_GROUP does not exist.${NC}"
    exit 0
fi

echo -e "${YELLOW}Deleting resource group and all resources...${NC}"

# Delete the entire resource group
az group delete --name $RESOURCE_GROUP --yes --no-wait

echo -e "${GREEN}Cleanup initiated. Resources are being deleted in the background.${NC}"
echo -e "${GREEN}You can check the status with: az group show --name $RESOURCE_GROUP${NC}"
echo -e "${YELLOW}Note: This does not delete your Neo4j AuraDB instance. Please delete it manually if needed.${NC}"