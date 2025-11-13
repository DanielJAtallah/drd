# Example: Create a GCS bucket for data storage
resource "google_storage_bucket" "data_bucket" {
  name          = "${var.project_id}-reddit-data"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Output the bucket name
output "data_bucket_name" {
  value       = google_storage_bucket.data_bucket.name
  description = "Name of the data storage bucket"
}