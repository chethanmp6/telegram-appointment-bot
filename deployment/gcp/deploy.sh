#!/bin/bash

# Google Cloud Deployment Script for Appointment Bot
set -e

# Configuration
ENVIRONMENT=${1:-dev}
PROJECT_ID=${2:-""}
REGION=${REGION:-us-central1}

echo "🚀 Deploying Appointment Bot to Google Cloud"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

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

# Validation
if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required. Usage: ./deploy.sh <environment> <project-id>"
    exit 1
fi

# Check required tools
for tool in gcloud terraform docker; do
    if ! command -v $tool &> /dev/null; then
        print_error "$tool is not installed. Please install it first."
        exit 1
    fi
done

# Authenticate with gcloud
print_info "Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    print_warning "Please authenticate with Google Cloud:"
    gcloud auth login
fi

# Set project
gcloud config set project $PROJECT_ID
print_status "Project set to $PROJECT_ID"

# Step 1: Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure with Terraform..."
cd deployment/gcp/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan \
    -var="project_id=$PROJECT_ID" \
    -var="region=$REGION" \
    -var="environment=$ENVIRONMENT" \
    -out=tfplan

# Apply deployment
terraform apply tfplan

# Get outputs
VPC_CONNECTOR=$(terraform output -raw vpc_connector_name)
POSTGRES_INSTANCE=$(terraform output -raw postgres_instance_name)
POSTGRES_IP=$(terraform output -raw postgres_private_ip)
REDIS_HOST=$(terraform output -raw redis_host)
SERVICE_ACCOUNT=$(terraform output -raw cloud_run_service_account)

print_status "Infrastructure deployed successfully"

cd ../../..

# Step 2: Set manual secrets
echo "🔐 Setting up secrets..."

manual_secrets=(
    "neo4j-uri"
    "neo4j-password"
    "openai-api-key"
    "anthropic-api-key"
    "telegram-bot-token"
    "pinecone-api-key"
)

print_warning "Please set these secrets manually in Google Secret Manager:"
for secret in "${manual_secrets[@]}"; do
    echo "   gcloud secrets versions add $secret --data-file=-"
    echo "   (Enter the secret value and press Ctrl+D)"
done

echo ""
read -p "Have you set all the manual secrets? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please set the secrets and run the script again."
    exit 1
fi

# Step 3: Build and deploy with Cloud Build
echo "🏗️  Building and deploying application..."

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Submit build
gcloud builds submit \
    --config=deployment/gcp/cloudbuild.yml \
    --substitutions=_REGION=$REGION,_VPC_CONNECTOR=$VPC_CONNECTOR \
    .

print_status "Application deployed to Cloud Run"

# Step 4: Get service URLs
echo "📋 Getting service information..."

APP_URL=$(gcloud run services describe appointment-bot \
    --region=$REGION \
    --format='value(status.url)')

WORKER_URL=$(gcloud run services describe appointment-bot-worker \
    --region=$REGION \
    --format='value(status.url)' 2>/dev/null || echo "Not deployed")

print_status "Services deployed successfully"

# Step 5: Initialize database
echo "🗄️  Initializing database..."

# Wait a moment for services to be ready
sleep 30

# Initialize database
curl -X POST "$APP_URL/debug/reset-database" || print_warning "Database initialization may have failed"

print_status "Database initialization attempted"

# Step 6: Test deployment
echo "🧪 Testing deployment..."

# Health check
HEALTH_RESPONSE=$(curl -s "$APP_URL/health" || echo "Health check failed")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_status "Health check passed"
else
    print_warning "Health check may have issues: $HEALTH_RESPONSE"
fi

# Step 7: Configure monitoring (optional)
echo "📊 Setting up monitoring..."

# Create log-based metrics
gcloud logging metrics create appointment_bot_errors \
    --description="Count of application errors" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="appointment-bot" AND severity>=ERROR' \
    --project=$PROJECT_ID 2>/dev/null || print_warning "Log metric may already exist"

print_status "Basic monitoring configured"

# Summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "🌐 Service URLs:"
echo "Main App: $APP_URL"
echo "Worker: $WORKER_URL"
echo ""
echo "🔗 Important Links:"
echo "Health Check: $APP_URL/health"
echo "API Docs: $APP_URL/docs"
echo "Logs: https://console.cloud.google.com/run/detail/$REGION/appointment-bot/logs?project=$PROJECT_ID"
echo ""
echo "🗄️  Database Info:"
echo "Instance: $POSTGRES_INSTANCE"
echo "Private IP: $POSTGRES_IP"
echo "Redis Host: $REDIS_HOST"
echo ""
echo "📋 Next Steps:"
echo "1. Test the health endpoint: curl $APP_URL/health"
echo "2. Upload knowledge base documents via API"
echo "3. Test the Telegram bot"
echo "4. Set up custom domain (optional)"
echo "5. Configure SSL certificate (optional)"
echo ""
echo "🔧 Useful Commands:"
echo "View logs: gcloud run services logs tail appointment-bot --region=$REGION"
echo "Update service: gcloud run deploy appointment-bot --region=$REGION"
echo "Scale service: gcloud run services update appointment-bot --region=$REGION --max-instances=20"

print_status "Google Cloud deployment completed!"

# Optional: Set up custom domain
echo ""
read -p "Would you like to set up a custom domain? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name: " DOMAIN_NAME
    
    if [ ! -z "$DOMAIN_NAME" ]; then
        print_info "Setting up domain mapping..."
        
        gcloud run domain-mappings create \
            --service=appointment-bot \
            --domain=$DOMAIN_NAME \
            --region=$REGION
        
        print_status "Domain mapping created. Please configure DNS:"
        echo "Add a CNAME record pointing $DOMAIN_NAME to:"
        gcloud run domain-mappings describe $DOMAIN_NAME \
            --region=$REGION \
            --format='value(status.resourceRecords[0].rrdata)'
    fi
fi

echo ""
print_status "All done! 🚀"