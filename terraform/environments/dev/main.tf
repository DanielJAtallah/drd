terraform {
  required_version = ">= 1.9.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Use the storage module
module "reddit_data_storage" {
  source = "../../modules/storage"

  project_id        = var.project_id
  environment       = var.environment
  region            = var.region
  bucket_suffix     = "reddit-data"
  lifecycle_age_days = 30  # Shorter retention for dev
}

# Outputs
output "data_bucket_name" {
  value       = module.reddit_data_storage.bucket_name
  description = "Name of the data storage bucket"
}