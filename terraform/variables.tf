variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "drd-dev"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}