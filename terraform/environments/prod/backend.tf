terraform {
  backend "gcs" {
    bucket = "drd-prod-terraform-state"
    prefix = "terraform/state"
  }
}