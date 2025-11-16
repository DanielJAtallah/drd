variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "bucket_suffix" {
  description = "Suffix for bucket name"
  type        = string
}

variable "lifecycle_age_days" {
  description = "Days before objects are deleted"
  type        = number
  default     = 90
}