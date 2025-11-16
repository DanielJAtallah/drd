output "bucket_name" {
  value       = google_storage_bucket.data_bucket.name
  description = "Name of the created bucket"
}

output "bucket_url" {
  value       = google_storage_bucket.data_bucket.url
  description = "URL of the created bucket"
}