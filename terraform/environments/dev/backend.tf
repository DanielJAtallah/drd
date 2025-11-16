terraform {
  backend "gcs" {
    bucket = "drd-dev-terraform-state"
    prefix = "terraform/state"
  }
}