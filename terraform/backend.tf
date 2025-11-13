terraform {
  backend "gcs" {
    bucket = "drd-terraform-state"
    prefix = "terraform/state"
  }
}