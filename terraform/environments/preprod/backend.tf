terraform {
  backend "gcs" {
    bucket = "drd-preprod-terraform-state"
    prefix = "terraform/state"
  }
}