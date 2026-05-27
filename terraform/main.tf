provider "aws" {
  region = "ap-south-1"
}

resource "aws_ecs_cluster" "sentinel_cluster" {
  name = "senintel-production-cluster"
}

resource "aws_s3_bucket" "document_storage" {
  bucket = "canara-sentinel-documents-prod"
}

# Production VPC and Load Balancers go here
