#!/bin/bash

# AWS Credentials (Informational Only - Do not hardcode sensitive keys here)
AWS_ACCOUNT_NAME="Quanty"
AWS_EMAIL="bensmatt3@gmail.com"
AWS_ACCOUNT_ID="116981797342"
AWS_CANONICAL_USER_ID="13a03d49abd12badde3e7568e9a03536cb729f5ab173f5fdb6a0c84ceb5d172e"

# EC2 Instance Details
INSTANCE_NAME="Quanty"
INSTANCE_ID="i-0d212a09edc5fe81e"
INSTANCE_STATE="Running"
INSTANCE_TYPE="t2.micro"
REGION="us-east-2"
PUBLIC_IP="18.220.107.72"
PUBLIC_DNS="ec2-18-220-107-72.us-east-2.compute.amazonaws.com"
KEY_NAME="quantyconnect"
SECURITY_GROUP="launch-wizard-1"
ECR_REPO_NAME="trading-bot"

# Build Docker image
echo "Building Docker image..."
docker build -t $ECR_REPO_NAME .

# Authenticate Docker to AWS ECR
echo "Authenticating Docker to AWS ECR..."
aws ecr get-login-password --region $REGION --profile quanty | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag Docker image
echo "Tagging Docker image..."
docker tag $ECR_REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Push Docker image to AWS ECR
echo "Pushing Docker image to AWS ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Deploy to AWS ECS
echo "Deploying to AWS ECS..."
aws ecs update-service --cluster trading-bot-cluster --service trading-bot-service --force-new-deployment --profile quanty

# Print AWS and instance details
echo "AWS Account Details:"
echo "-------------------"
echo "Account Name: $AWS_ACCOUNT_NAME"
echo "Email Address: $AWS_EMAIL"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "Canonical User ID: $AWS_CANONICAL_USER_ID"

echo "Instance Details:"
echo "-----------------"
echo "Name: $INSTANCE_NAME"
echo "Instance ID: $INSTANCE_ID"
echo "Instance State: $INSTANCE_STATE"
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo "Public IPv4 DNS: $PUBLIC_DNS"
echo "Public IPv4 Address: $PUBLIC_IP"
echo "Key Name: $KEY_NAME"
echo "Security Group: $SECURITY_GROUP"
