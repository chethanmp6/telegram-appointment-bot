# 🚀 Quick Start Cloud Deployment

Get your Telegram Appointment Bot running in the cloud in under 30 minutes!

## 🎯 Choose Your Path

### Option 1: AWS (Recommended for Enterprise) 
**Best for**: Scalability, enterprise features, comprehensive services
```bash
./deployment/aws/deploy.sh prod
```

### Option 2: Google Cloud (Recommended for Startups)
**Best for**: Simplicity, cost-effectiveness, serverless
```bash
./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID
```

### Option 3: Kubernetes (Any Cloud)
**Best for**: Multi-cloud, container orchestration, flexibility
```bash
kubectl apply -f deployment/kubernetes/
```

---

## 🔥 Super Quick AWS Deployment

### Prerequisites (5 minutes)
```bash
# 1. Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# 2. Configure AWS
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Format (json)

# 3. Clone repository
git clone <your-repo-url>
cd AppointmentManager
```

### Get Your API Keys (5 minutes)
1. **Telegram Bot**: Message @BotFather → `/newbot` → Get token
2. **OpenAI**: Visit platform.openai.com → API Keys → Create new
3. **Pinecone**: Visit pinecone.io → Sign up → Get API key

### Deploy! (15 minutes)
```bash
# Make script executable
chmod +x deployment/aws/deploy.sh

# Deploy everything
./deployment/aws/deploy.sh prod

# The script will:
# ✅ Create infrastructure (VPC, RDS, Redis, ECS)
# ✅ Build and push Docker image
# ✅ Deploy application
# ✅ Set up monitoring
# ✅ Configure webhook
```

### Set Your Secrets (3 minutes)
```bash
# Set your API keys (replace with actual values)
aws ssm put-parameter --name "/appointment-bot/openai/api-key" --value "sk-your-openai-key" --type "SecureString"
aws ssm put-parameter --name "/appointment-bot/telegram/bot-token" --value "your-telegram-token" --type "SecureString"
aws ssm put-parameter --name "/appointment-bot/pinecone/api-key" --value "your-pinecone-key" --type "SecureString"
aws ssm put-parameter --name "/appointment-bot/business-name" --value "Your Business Name" --type "String"

# Optional: Set up Neo4j AuraDB (recommended)
aws ssm put-parameter --name "/appointment-bot/neo4j/uri" --value "bolt+s://your-aura-instance.databases.neo4j.io" --type "String"
aws ssm put-parameter --name "/appointment-bot/neo4j/password" --value "your-neo4j-password" --type "SecureString"
```

### Test & Initialize (2 minutes)
```bash
# Get your app URL (from deployment output)
APP_URL="http://your-load-balancer-url"

# Test health
curl $APP_URL/health

# Initialize database
curl -X POST $APP_URL/debug/reset-database

# Your bot is live! Test it on Telegram 🎉
```

---

## ⚡ Super Quick GCP Deployment

### Prerequisites (5 minutes)
```bash
# 1. Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 2. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Clone repository
git clone <your-repo-url>
cd AppointmentManager
```

### Deploy Infrastructure (10 minutes)
```bash
cd deployment/gcp/terraform

# Initialize and deploy
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" -auto-approve

cd ../../..
```

### Set Secrets (3 minutes)
```bash
# Store secrets in Secret Manager
echo "sk-your-openai-key" | gcloud secrets create openai-api-key --data-file=-
echo "your-telegram-token" | gcloud secrets create telegram-bot-token --data-file=-
echo "your-pinecone-key" | gcloud secrets create pinecone-api-key --data-file=-
echo "Your Business Name" | gcloud secrets create business-name --data-file=-

# Optional: Neo4j AuraDB
echo "bolt+s://your-aura.databases.neo4j.io" | gcloud secrets create neo4j-uri --data-file=-
echo "your-neo4j-password" | gcloud secrets create neo4j-password --data-file=-
```

### Deploy Application (10 minutes)
```bash
# Deploy with Cloud Build
chmod +x deployment/gcp/deploy.sh
./deployment/gcp/deploy.sh prod YOUR_PROJECT_ID

# Your app will be deployed to Cloud Run automatically! 🚀
```

---

## 🐳 Super Quick Kubernetes Deployment

### Prerequisites (5 minutes)
```bash
# Ensure you have a Kubernetes cluster and kubectl configured
kubectl cluster-info

# Clone repository
git clone <your-repo-url>
cd AppointmentManager
```

### Configure Secrets (5 minutes)
```bash
# Edit the secrets file
nano deployment/kubernetes/secrets.yml

# Update these values:
# - OPENAI_API_KEY: "sk-your-openai-key"
# - TELEGRAM_BOT_TOKEN: "your-telegram-token"
# - PINECONE_API_KEY: "your-pinecone-key"
# - BUSINESS_NAME: "Your Business Name"
# - And database connection details
```

### Deploy Everything (10 minutes)
```bash
# Deploy all components
kubectl apply -f deployment/kubernetes/namespace.yml
kubectl apply -f deployment/kubernetes/secrets.yml
kubectl apply -f deployment/kubernetes/configmap.yml

# Deploy databases (if not using managed services)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql --namespace appointment-bot --set auth.postgresPassword=yourpassword
helm install redis bitnami/redis --namespace appointment-bot --set auth.password=yourpassword

# Deploy application
kubectl apply -f deployment/kubernetes/deployment.yml
kubectl apply -f deployment/kubernetes/service.yml
kubectl apply -f deployment/kubernetes/ingress.yml

# Check status
kubectl get pods -n appointment-bot
```

### Access Your App (2 minutes)
```bash
# Get the external IP
kubectl get ingress -n appointment-bot

# Or use port forwarding for testing
kubectl port-forward svc/appointment-bot-service 8080:80 -n appointment-bot

# Test: http://localhost:8080/health
```

---

## 🛠️ Post-Deployment Setup

### 1. Upload Knowledge Base (5 minutes)
```bash
# Upload your business documents
curl -X POST "$APP_URL/api/v1/knowledge/documents/upload" \
  -F "files=@your-business-policies.pdf" \
  -F "document_type=policy" \
  -F "category=business"

# Upload FAQ
curl -X POST "$APP_URL/api/v1/knowledge/documents/upload" \
  -F "files=@your-faq.txt" \
  -F "document_type=faq" \
  -F "category=support"
```

### 2. Create Sample Services (3 minutes)
```bash
# Create services via API
curl -X POST "$APP_URL/api/v1/appointments/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Haircut",
    "description": "Professional haircut service",
    "duration": 60,
    "price": 50.0,
    "category": "hair"
  }'

curl -X POST "$APP_URL/api/v1/appointments/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Massage",
    "description": "Relaxing full body massage",
    "duration": 90,
    "price": 120.0,
    "category": "wellness"
  }'
```

### 3. Create Staff Members (2 minutes)
```bash
# Create staff via API
curl -X POST "$APP_URL/api/v1/appointments/staff" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "email": "sarah@yourbusiness.com",
    "specializations": ["haircut", "styling"],
    "working_hours": {
      "monday": "9:00-17:00",
      "tuesday": "9:00-17:00",
      "wednesday": "9:00-17:00",
      "thursday": "9:00-17:00",
      "friday": "9:00-17:00"
    }
  }'
```

### 4. Test Your Bot! (2 minutes)
1. Open Telegram
2. Search for your bot (@your_bot_name)
3. Send `/start`
4. Try: "I need a haircut next Friday"
5. Book an appointment! 🎉

---

## 📊 Monitoring URLs

After deployment, bookmark these URLs:

### AWS
- **Application**: `http://your-alb-dns-name`
- **Health Check**: `http://your-alb-dns-name/health`
- **API Docs**: `http://your-alb-dns-name/docs`
- **Logs**: AWS CloudWatch Console

### GCP
- **Application**: `https://your-service-url.run.app`
- **Health Check**: `https://your-service-url.run.app/health`
- **API Docs**: `https://your-service-url.run.app/docs`
- **Logs**: Google Cloud Console → Cloud Run

### Kubernetes
- **Application**: `https://your-ingress-domain`
- **Health Check**: `https://your-ingress-domain/health`
- **API Docs**: `https://your-ingress-domain/docs`
- **Flower (Celery)**: `https://flower.your-domain`

---

## 🔧 Quick Commands

### Restart Application
```bash
# AWS
aws ecs update-service --cluster appointment-bot --service appointment-bot-service --force-new-deployment

# GCP
gcloud run deploy appointment-bot --image gcr.io/PROJECT_ID/appointment-bot:latest

# Kubernetes
kubectl rollout restart deployment/appointment-bot-app -n appointment-bot
```

### View Logs
```bash
# AWS
aws logs tail /aws/ecs/appointment-bot --follow

# GCP
gcloud run services logs tail appointment-bot --follow

# Kubernetes
kubectl logs -f deployment/appointment-bot-app -n appointment-bot
```

### Scale Application
```bash
# AWS
aws ecs update-service --cluster appointment-bot --service appointment-bot-service --desired-count 3

# GCP (auto-scales based on traffic)
gcloud run services update appointment-bot --max-instances 10

# Kubernetes
kubectl scale deployment appointment-bot-app --replicas=3 -n appointment-bot
```

---

## 🆘 Quick Troubleshooting

### Bot Not Responding?
```bash
# Check webhook
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"

# Reset webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=https://your-domain.com/webhook/your-secret"
```

### Database Connection Issues?
```bash
# Test database connectivity
curl $APP_URL/health

# Check logs for database errors
# Follow the "View Logs" commands above
```

### High Memory Usage?
```bash
# Check resource usage
# AWS: CloudWatch Metrics
# GCP: Cloud Monitoring
# K8s: kubectl top pods -n appointment-bot
```

---

## 💡 Pro Tips

1. **Start Small**: Use development environment first
2. **Monitor Costs**: Set up billing alerts
3. **Backup Regularly**: Enable automated backups
4. **Use HTTPS**: Set up SSL certificates
5. **Monitor Health**: Set up alerts for downtime
6. **Scale Gradually**: Start with minimal resources
7. **Test Everything**: Use health checks extensively
8. **Keep Secrets Safe**: Never commit API keys

---

## 🎉 You're Live!

Congratulations! Your Telegram Appointment Bot is now running in the cloud with:

✅ **Multi-database architecture** (PostgreSQL + Neo4j + Vector DB)  
✅ **Intelligent AI agent** with function calling  
✅ **Graph-based recommendations**  
✅ **Natural language processing**  
✅ **Auto-scaling infrastructure**  
✅ **Production monitoring**  
✅ **Secure secret management**  

### Next Steps:
1. 📱 Test your bot on Telegram
2. 📚 Upload your business knowledge base
3. 👥 Add your staff and services
4. 📊 Monitor usage and performance
5. 🚀 Scale as your business grows

**Need help?** Check the full [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed instructions.