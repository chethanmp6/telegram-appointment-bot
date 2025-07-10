# Cloud Deployment Guide

This comprehensive guide covers deploying the Telegram Appointment Bot to AWS, Google Cloud Platform, and Azure, as well as Kubernetes clusters.

## 📋 Prerequisites

### Required Tools
- Docker
- Git
- Cloud CLI tools (AWS CLI, gcloud, or Azure CLI)
- kubectl (for Kubernetes deployments)
- Terraform (for infrastructure as code)

### Required Accounts & Services
- Cloud provider account (AWS/GCP/Azure)
- Telegram Bot Token (from @BotFather)
- OpenAI or Anthropic API key
- Neo4j AuraDB account (recommended) or self-hosted Neo4j
- Vector database service (Pinecone recommended)

## 🚀 Quick Start

### 1. Choose Your Cloud Provider

#### AWS (Recommended for Enterprise)
```bash
# Clone and navigate
git clone <your-repo>
cd AppointmentManager

# Configure AWS credentials
aws configure

# Deploy
chmod +x deployment/aws/deploy.sh
./deployment/aws/deploy.sh prod
```

#### Google Cloud Platform
```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy
chmod +x deployment/gcp/deploy.sh
./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID
```

#### Azure
```bash
# Login to Azure
az login

# Deploy
chmod +x deployment/azure/deploy.sh
./deployment/azure/deploy.sh prod
```

## ☁️ Cloud-Specific Deployment

### 🟡 AWS Deployment

**Architecture**: ECS Fargate + RDS + ElastiCache + Neo4j AuraDB

#### Step-by-Step AWS Deployment

1. **Prerequisites**
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Configure credentials
   aws configure
   ```

2. **Set Environment Variables**
   ```bash
   export AWS_REGION=us-east-1
   export ENVIRONMENT=prod
   ```

3. **Deploy Infrastructure**
   ```bash
   # Deploy CloudFormation stack
   aws cloudformation deploy \
     --template-file deployment/aws/cloudformation.yml \
     --stack-name prod-appointment-bot \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides Environment=prod
   ```

4. **Configure Secrets**
   ```bash
   # Store secrets in AWS Systems Manager Parameter Store
   aws ssm put-parameter \
     --name "/appointment-bot/openai/api-key" \
     --value "your-openai-key" \
     --type "SecureString"
   
   aws ssm put-parameter \
     --name "/appointment-bot/telegram/bot-token" \
     --value "your-telegram-bot-token" \
     --type "SecureString"
   ```

5. **Deploy Application**
   ```bash
   ./deployment/aws/deploy.sh prod
   ```

#### AWS Services Used
- **ECS Fargate**: Container hosting
- **RDS PostgreSQL**: Primary database
- **ElastiCache Redis**: Caching and queues
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Logging and monitoring
- **Systems Manager**: Secret management
- **ECR**: Container registry

#### AWS Costs (Estimated Monthly)
- **Development**: $50-100/month
- **Production**: $200-500/month
- **Enterprise**: $500-1000+/month

### 🔵 Google Cloud Platform Deployment

**Architecture**: Cloud Run + Cloud SQL + Memorystore + Neo4j AuraDB

#### Step-by-Step GCP Deployment

1. **Prerequisites**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Authenticate
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy with Terraform**
   ```bash
   cd deployment/gcp/terraform
   
   # Initialize Terraform
   terraform init
   
   # Plan deployment
   terraform plan -var="project_id=YOUR_PROJECT_ID"
   
   # Apply deployment
   terraform apply -var="project_id=YOUR_PROJECT_ID"
   ```

3. **Set Secrets**
   ```bash
   # Store secrets in Secret Manager
   echo "your-openai-key" | gcloud secrets create openai-api-key --data-file=-
   echo "your-telegram-token" | gcloud secrets create telegram-bot-token --data-file=-
   ```

4. **Deploy Application**
   ```bash
   ./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID
   ```

#### GCP Services Used
- **Cloud Run**: Serverless containers
- **Cloud SQL**: Managed PostgreSQL
- **Memorystore Redis**: Managed Redis
- **Cloud Build**: CI/CD
- **Secret Manager**: Secret storage
- **VPC**: Networking
- **Cloud Logging**: Monitoring

#### GCP Costs (Estimated Monthly)
- **Development**: $30-80/month
- **Production**: $150-400/month
- **Enterprise**: $400-800+/month

### 🔴 Azure Deployment

**Architecture**: Container Instances + Azure Database + Redis Cache + Neo4j AuraDB

#### Step-by-Step Azure Deployment

1. **Prerequisites**
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login
   az login
   ```

2. **Deploy Infrastructure**
   ```bash
   # Create resource group
   az group create --name appointment-bot-rg --location "East US"
   
   # Deploy ARM template
   az deployment group create \
     --resource-group appointment-bot-rg \
     --template-file deployment/azure/azuredeploy.json \
     --parameters @deployment/azure/azuredeploy.parameters.json
   ```

3. **Deploy Application**
   ```bash
   ./deployment/azure/deploy.sh prod
   ```

#### Azure Services Used
- **Container Instances**: Container hosting
- **Azure Database for PostgreSQL**: Managed database
- **Azure Cache for Redis**: Managed Redis
- **Application Gateway**: Load balancing
- **Key Vault**: Secret management
- **Container Registry**: Image storage

## 🐳 Kubernetes Deployment

### Universal Kubernetes Deployment

Works on EKS, GKE, AKS, or any Kubernetes cluster.

#### Prerequisites
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/
```

#### Deploy to Kubernetes

1. **Update Configuration**
   ```bash
   # Edit secrets and config
   kubectl apply -f deployment/kubernetes/namespace.yml
   kubectl apply -f deployment/kubernetes/secrets.yml
   kubectl apply -f deployment/kubernetes/configmap.yml
   ```

2. **Deploy Database Services** (if not using managed services)
   ```bash
   # Deploy PostgreSQL
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm install postgres bitnami/postgresql \
     --namespace appointment-bot \
     --set auth.postgresPassword=yourpassword
   
   # Deploy Redis
   helm install redis bitnami/redis \
     --namespace appointment-bot \
     --set auth.password=yourpassword
   
   # Deploy Neo4j
   helm repo add neo4j https://helm.neo4j.com/neo4j
   helm install neo4j neo4j/neo4j \
     --namespace appointment-bot \
     --set neo4j.password=yourpassword
   ```

3. **Deploy Application**
   ```bash
   kubectl apply -f deployment/kubernetes/deployment.yml
   kubectl apply -f deployment/kubernetes/service.yml
   kubectl apply -f deployment/kubernetes/ingress.yml
   ```

#### Kubernetes Cluster Options

##### Amazon EKS
```bash
# Create EKS cluster
eksctl create cluster \
  --name appointment-bot \
  --version 1.27 \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4
```

##### Google GKE
```bash
# Create GKE cluster
gcloud container clusters create appointment-bot \
  --zone us-central1-a \
  --machine-type e2-medium \
  --num-nodes 2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 4
```

##### Azure AKS
```bash
# Create AKS cluster
az aks create \
  --resource-group appointment-bot-rg \
  --name appointment-bot \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token | `123456:ABC...` |
| `POSTGRES_HOST` | Yes | PostgreSQL host | `localhost` |
| `NEO4J_URI` | Yes | Neo4j connection URI | `bolt://localhost:7687` |
| `PINECONE_API_KEY` | No | Pinecone API key | `abc123...` |
| `BUSINESS_NAME` | No | Your business name | `My Salon` |

### Secret Management

#### AWS
```bash
# Store in Parameter Store
aws ssm put-parameter \
  --name "/appointment-bot/openai/api-key" \
  --value "your-key" \
  --type "SecureString"
```

#### GCP
```bash
# Store in Secret Manager
echo "your-key" | gcloud secrets create openai-api-key --data-file=-
```

#### Azure
```bash
# Store in Key Vault
az keyvault secret set \
  --vault-name appointment-bot-kv \
  --name openai-api-key \
  --value "your-key"
```

#### Kubernetes
```bash
# Create secret
kubectl create secret generic appointment-bot-secrets \
  --namespace appointment-bot \
  --from-literal=OPENAI_API_KEY=your-key \
  --from-literal=TELEGRAM_BOT_TOKEN=your-token
```

## 🔐 Security Best Practices

### Network Security
- Use private subnets for databases
- Implement network policies in Kubernetes
- Configure firewall rules properly
- Use VPC/VNET peering for services

### Application Security
- Store all secrets in cloud-native secret managers
- Use HTTPS/TLS everywhere
- Implement proper authentication
- Regular security scanning of containers

### Database Security
- Enable encryption at rest and in transit
- Use strong passwords
- Limit network access
- Regular backups with encryption

## 📊 Monitoring & Observability

### Health Checks
```bash
# Check application health
curl https://your-domain.com/health

# Check specific components
curl https://your-domain.com/api/v1/graph/health
curl https://your-domain.com/api/v1/knowledge/health
```

### Logging

#### AWS CloudWatch
```bash
# View logs
aws logs tail /aws/ecs/appointment-bot --follow
```

#### GCP Cloud Logging
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision"
```

#### Azure Monitor
```bash
# View logs
az monitor log-analytics query \
  --workspace appointment-bot-workspace \
  --analytics-query "ContainerLog | limit 100"
```

#### Kubernetes
```bash
# View logs
kubectl logs -f deployment/appointment-bot-app -n appointment-bot
kubectl logs -f deployment/appointment-bot-worker -n appointment-bot
```

### Metrics & Alerts

Set up alerts for:
- Application response time > 2s
- Error rate > 5%
- Database connection failures
- Memory usage > 80%
- CPU usage > 70%

## 🚦 CI/CD Pipeline

### GitHub Actions

The included GitHub Actions workflow provides:
- Automated testing
- Security scanning
- Multi-cloud deployment
- Notifications

### Setup Steps

1. **Configure Secrets in GitHub**
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   GCP_SA_KEY
   AZURE_CREDENTIALS
   TELEGRAM_BOT_TOKEN
   OPENAI_API_KEY
   ```

2. **Configure Variables**
   ```
   AWS_REGION
   GCP_PROJECT_ID
   GCP_REGION
   AZURE_RESOURCE_GROUP
   AZURE_LOCATION
   ```

3. **Trigger Deployment**
   - Push to `main` branch for production
   - Use workflow dispatch for manual deployments

## 🔄 Scaling & Performance

### Horizontal Scaling

#### AWS ECS
```bash
# Scale ECS service
aws ecs update-service \
  --cluster appointment-bot \
  --service appointment-bot-service \
  --desired-count 5
```

#### GCP Cloud Run
```bash
# Auto-scales based on traffic
# Configure max instances in deployment
```

#### Kubernetes
```bash
# Scale deployment
kubectl scale deployment appointment-bot-app \
  --namespace appointment-bot \
  --replicas=5

# Set up HPA
kubectl autoscale deployment appointment-bot-app \
  --namespace appointment-bot \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

### Database Scaling

#### PostgreSQL
- Use read replicas for read-heavy workloads
- Consider connection pooling (PgBouncer)
- Monitor query performance

#### Neo4j
- Use Neo4j clustering for high availability
- Optimize Cypher queries
- Consider caching frequently accessed data

#### Redis
- Use Redis clustering for larger datasets
- Implement proper cache invalidation
- Monitor memory usage

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check network connectivity
telnet your-db-host 5432

# Check credentials
psql -h your-db-host -U postgres -d appointment_bot
```

#### LLM API Errors
```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### Telegram Webhook Issues
```bash
# Check webhook status
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"

# Set webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/webhook/secret"}'
```

### Performance Issues

#### High Memory Usage
- Check for memory leaks in application logs
- Increase container memory limits
- Optimize database queries

#### Slow Response Times
- Check database query performance
- Monitor LLM API response times
- Verify network latency

#### High Error Rates
- Check application logs for exceptions
- Verify all secrets are correctly configured
- Test database connectivity

## 💰 Cost Optimization

### AWS Cost Optimization
- Use Spot instances for development
- Right-size ECS tasks
- Set up CloudWatch billing alerts
- Use Reserved Instances for production

### GCP Cost Optimization
- Use preemptible VMs
- Set up budget alerts
- Optimize Cloud Run concurrency
- Use committed use discounts

### Azure Cost Optimization
- Use Azure Cost Management
- Set up spending limits
- Use reserved instances
- Monitor resource utilization

### General Tips
- Use development environments for testing
- Clean up unused resources regularly
- Monitor costs daily
- Implement auto-shutdown for dev environments

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API](https://platform.openai.com/docs)
- [Neo4j Documentation](https://neo4j.com/docs/)

### Cloud Provider Docs
- [AWS ECS](https://docs.aws.amazon.com/ecs/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)

### Monitoring & Observability
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Jaeger](https://www.jaegertracing.io/docs/)

## 🆘 Support

### Getting Help
1. Check the logs first
2. Review the health check endpoints
3. Verify all configuration values
4. Test individual components
5. Check network connectivity

### Community Resources
- GitHub Issues
- Stack Overflow
- Cloud provider support
- Technology-specific communities

### Production Support
For production deployments, consider:
- Professional support contracts
- Monitoring services
- Backup and disaster recovery plans
- Security audits
- Performance optimization reviews