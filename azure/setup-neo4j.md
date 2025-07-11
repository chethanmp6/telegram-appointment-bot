# Neo4j AuraDB Setup for Azure Deployment

## Overview
Since Azure doesn't have a managed Neo4j service, we'll use Neo4j AuraDB (managed cloud service) for graph database functionality.

## Steps to Set Up Neo4j AuraDB

### 1. Create Neo4j AuraDB Instance
1. Go to [Neo4j AuraDB Console](https://console.neo4j.io)
2. Sign up/login to your Neo4j account
3. Click "Create Database"
4. Choose "AuraDB Free" (for development) or "AuraDB Professional" (for production)
5. Configure:
   - Database name: `appointment-bot-graph`
   - Region: Choose closest to your Azure region (East US recommended)
   - Initial password: Generate a strong password

### 2. Configure Connection
After database creation, you'll get:
- **Connection URI**: `neo4j+s://xxxxxxxx.databases.neo4j.io`
- **Username**: `neo4j`
- **Password**: Your chosen password

### 3. Update Azure Parameters
Update the following in `azure/bicep/parameters.json`:
```json
{
  "neo4jUri": {
    "value": "neo4j+s://your-database-id.databases.neo4j.io"
  },
  "neo4jUsername": {
    "value": "neo4j"
  },
  "neo4jPassword": {
    "value": "your-database-password"
  }
}
```

### 4. Configure Firewall (if using Professional)
1. In Neo4j Console, go to your database
2. Navigate to "Connection" tab
3. Add your Azure Container App IP ranges (or use 0.0.0.0/0 for all IPs)

### 5. Initialize Database Schema
After deployment, run the initialization:
```bash
# Get your Container App URL
APP_URL=$(az containerapp show --name appointment-bot --resource-group appointment-bot-rg --query properties.configuration.ingress.fqdn --output tsv)

# Initialize Neo4j schema
curl -X POST https://$APP_URL/api/v1/graph/init
```

## Alternative: Self-hosted Neo4j on Azure

If you prefer self-hosted Neo4j:

### Option 1: Azure Container Instances
```bash
# Deploy Neo4j container
az container create \
    --resource-group appointment-bot-rg \
    --name neo4j-db \
    --image neo4j:5.15 \
    --cpu 2 \
    --memory 4 \
    --ports 7474 7687 \
    --environment-variables \
        NEO4J_AUTH=neo4j/your-password \
        NEO4J_PLUGINS=["apoc"] \
    --dns-name-label appointment-neo4j
```

### Option 2: Azure VM with Neo4j
```bash
# Create VM
az vm create \
    --resource-group appointment-bot-rg \
    --name neo4j-vm \
    --image Ubuntu2204 \
    --size Standard_B2s \
    --admin-username azureuser \
    --generate-ssh-keys

# Install Neo4j (run on VM)
sudo apt update
sudo apt install -y openjdk-17-jre
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install -y neo4j
```

## Recommended Approach
For production deployments, **Neo4j AuraDB** is recommended because:
- Fully managed service
- Automatic backups
- Monitoring and alerting
- High availability
- No infrastructure management

## Cost Considerations
- **AuraDB Free**: Free tier with limitations
- **AuraDB Professional**: Pay-per-use pricing
- **Self-hosted**: Infrastructure costs + management overhead

Choose based on your requirements and budget.