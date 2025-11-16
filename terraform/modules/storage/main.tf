resource "google_storage_bucket" "data_bucket" {
  name          = "${var.project_id}-${var.bucket_suffix}"
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "prod" # Only allow force destroy in non-prod

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    project     = "drd"
  }
}