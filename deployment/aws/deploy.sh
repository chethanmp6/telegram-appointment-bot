#!/bin/bash

# AWS Deployment Script for Appointment Bot
set -e

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="appointment-bot"
STACK_NAME="${ENVIRONMENT}-appointment-bot"

echo "🚀 Deploying Appointment Bot to AWS"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

# Step 1: Create ECR repository if it doesn't exist
echo "📦 Setting up ECR repository..."
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION >/dev/null 2>&1; then
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    print_status "ECR repository created"
else
    print_status "ECR repository already exists"
fi

# Step 2: Build and push Docker image
echo "🐳 Building and pushing Docker image..."
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Build image
docker build -t $ECR_REPOSITORY_NAME:latest -f Dockerfile .

# Tag image
docker tag $ECR_REPOSITORY_NAME:latest $ECR_URI:latest
docker tag $ECR_REPOSITORY_NAME:latest $ECR_URI:$ENVIRONMENT

# Push image
docker push $ECR_URI:latest
docker push $ECR_URI:$ENVIRONMENT

print_status "Docker image pushed to ECR"

# Step 3: Store secrets in Parameter Store
echo "🔐 Setting up Parameter Store secrets..."

# Check if secrets exist, create them if they don't
declare -A secrets=(
    ["/appointment-bot/postgres/password"]="$(openssl rand -base64 32)"
    ["/appointment-bot/neo4j/password"]="$(openssl rand -base64 32)"
    ["/appointment-bot/secret-key"]="$(openssl rand -base64 64)"
    ["/appointment-bot/telegram/webhook-secret"]="$(openssl rand -base64 32)"
)

for param_name in "${!secrets[@]}"; do
    if ! aws ssm get-parameter --name "$param_name" --region $AWS_REGION >/dev/null 2>&1; then
        aws ssm put-parameter \
            --name "$param_name" \
            --value "${secrets[$param_name]}" \
            --type "SecureString" \
            --region $AWS_REGION
        print_status "Created parameter: $param_name"
    else
        print_warning "Parameter already exists: $param_name"
    fi
done

# These parameters need to be set manually
manual_params=(
    "/appointment-bot/openai/api-key"
    "/appointment-bot/telegram/bot-token"
    "/appointment-bot/pinecone/api-key"
    "/appointment-bot/anthropic/api-key"
)

echo ""
print_warning "⚠️  Please set these parameters manually in AWS Systems Manager Parameter Store:"
for param in "${manual_params[@]}"; do
    echo "   - $param"
done
echo ""

# Step 4: Deploy CloudFormation stack
echo "☁️  Deploying CloudFormation infrastructure..."

aws cloudformation deploy \
    --template-file deployment/aws/cloudformation.yml \
    --stack-name $STACK_NAME \
    --parameter-overrides Environment=$ENVIRONMENT \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION

print_status "Infrastructure deployed"

# Step 5: Get infrastructure outputs
echo "📋 Retrieving infrastructure details..."

VPC_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`VPC`].OutputValue' \
    --output text)

PRIVATE_SUBNETS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' \
    --output text)

ECS_CLUSTER=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSCluster`].OutputValue' \
    --output text)

TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroup`].OutputValue' \
    --output text)

RDS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`RDSEndpoint`].OutputValue' \
    --output text)

REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
    --output text)

LOAD_BALANCER_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text)

# Update Parameter Store with infrastructure endpoints
aws ssm put-parameter \
    --name "/appointment-bot/postgres/host" \
    --value "$RDS_ENDPOINT" \
    --type "String" \
    --overwrite \
    --region $AWS_REGION

aws ssm put-parameter \
    --name "/appointment-bot/redis/host" \
    --value "$REDIS_ENDPOINT" \
    --type "String" \
    --overwrite \
    --region $AWS_REGION

print_status "Infrastructure endpoints stored in Parameter Store"

# Step 6: Create and update ECS task definition
echo "📝 Creating ECS task definition..."

# Replace placeholders in task definition
sed "s/ACCOUNT_ID/$AWS_ACCOUNT_ID/g; s/REGION/$AWS_REGION/g" \
    deployment/aws/ecs-task-definition.json > /tmp/task-definition.json

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --region $AWS_REGION

print_status "ECS task definition registered"

# Step 7: Create ECS service
echo "🎯 Creating ECS service..."

# Check if service exists
if aws ecs describe-services \
    --cluster $ECS_CLUSTER \
    --services "appointment-bot-service" \
    --region $AWS_REGION \
    --query 'services[0].status' \
    --output text 2>/dev/null | grep -q "ACTIVE"; then
    
    # Update existing service
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service "appointment-bot-service" \
        --task-definition "appointment-bot" \
        --region $AWS_REGION
    
    print_status "ECS service updated"
else
    # Create new service
    aws ecs create-service \
        --cluster $ECS_CLUSTER \
        --service-name "appointment-bot-service" \
        --task-definition "appointment-bot" \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${ENVIRONMENT}-appointment-bot-ecs-sg" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)],assignPublicIp=DISABLED}" \
        --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=appointment-app,containerPort=8000" \
        --region $AWS_REGION
    
    print_status "ECS service created"
fi

# Step 8: Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $ECS_CLUSTER \
    --services "appointment-bot-service" \
    --region $AWS_REGION

print_status "Deployment completed successfully!"

# Step 9: Set up Telegram webhook
echo "🤖 Setting up Telegram webhook..."
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    print_warning "TELEGRAM_BOT_TOKEN not set. Please set the webhook manually:"
    echo "URL: ${LOAD_BALANCER_URL}/webhook/\$(WEBHOOK_SECRET)"
else
    WEBHOOK_SECRET=$(aws ssm get-parameter \
        --name "/appointment-bot/telegram/webhook-secret" \
        --with-decryption \
        --query 'Parameter.Value' \
        --output text \
        --region $AWS_REGION)
    
    curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"${LOAD_BALANCER_URL}/webhook/${WEBHOOK_SECRET}\"}"
    
    print_status "Telegram webhook configured"
fi

# Summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo "Environment: $ENVIRONMENT"
echo "ECS Cluster: $ECS_CLUSTER"
echo "Load Balancer URL: $LOAD_BALANCER_URL"
echo "Health Check: ${LOAD_BALANCER_URL}/health"
echo "API Docs: ${LOAD_BALANCER_URL}/docs"
echo ""
echo "📋 Next Steps:"
echo "1. Set manual parameters in Parameter Store:"
for param in "${manual_params[@]}"; do
    echo "   aws ssm put-parameter --name '$param' --value 'YOUR_VALUE' --type SecureString"
done
echo ""
echo "2. Initialize the database:"
echo "   curl -X POST ${LOAD_BALANCER_URL}/debug/reset-database"
echo ""
echo "3. Upload knowledge base documents via API"
echo ""
echo "4. Test the bot by messaging it on Telegram"

# Cleanup
rm -f /tmp/task-definition.json

print_status "Deployment script completed!"