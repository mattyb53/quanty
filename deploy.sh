#!/bin/bash

# Build Docker image
docker build -t trading-bot .

# Push Docker image to AWS ECR
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
docker tag trading-bot:latest your-account-id.dkr.ecr.your-region.amazonaws.com/trading-bot:latest
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/trading-bot:latest

# Deploy to AWS ECS
aws ecs update-service --cluster trading-bot-cluster --service trading-bot-service --force-new-deployment
