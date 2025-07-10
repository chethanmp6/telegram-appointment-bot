terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "business_name" {
  description = "Business name"
  type        = string
  default     = "Appointment Bot"
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "run.googleapis.com",
    "sql.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.environment}-appointment-bot-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "private_subnet" {
  name          = "${var.environment}-appointment-bot-private"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

# Private Service Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${var.environment}-appointment-bot-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${var.environment}-appointment-bot-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.0.2.0/28"
  
  depends_on = [google_project_service.apis]
}

# Cloud SQL (PostgreSQL)
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_database_instance" "postgres" {
  name             = "${var.environment}-appointment-bot-db"
  database_version = "POSTGRES_15"
  region          = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 20

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                              = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }

  deletion_protection = var.environment == "prod"
  depends_on         = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "database" {
  name     = "appointment_bot"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "user" {
  name     = "postgres"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Redis (Memorystore)
resource "google_redis_instance" "redis" {
  name           = "${var.environment}-appointment-bot-redis"
  memory_size_gb = 1
  region         = var.region

  authorized_network      = google_compute_network.vpc.id
  connect_mode           = "PRIVATE_SERVICE_ACCESS"
  redis_version          = "REDIS_7_0"
  display_name           = "Appointment Bot Redis"

  depends_on = [google_project_service.apis]
}

# Secrets
resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "postgres-host",
    "postgres-password",
    "neo4j-uri",
    "neo4j-password",
    "openai-api-key",
    "anthropic-api-key",
    "telegram-bot-token",
    "telegram-webhook-secret",
    "secret-key",
    "pinecone-api-key",
    "redis-host"
  ])

  secret_id = each.key
  
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

# Auto-generated secrets
resource "google_secret_manager_secret_version" "postgres_host" {
  secret      = google_secret_manager_secret.secrets["postgres-host"].id
  secret_data = google_sql_database_instance.postgres.private_ip_address
}

resource "google_secret_manager_secret_version" "postgres_password" {
  secret      = google_secret_manager_secret.secrets["postgres-password"].id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret_version" "redis_host" {
  secret      = google_secret_manager_secret.secrets["redis-host"].id
  secret_data = google_redis_instance.redis.host
}

resource "random_password" "secret_key" {
  length = 64
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secrets["secret-key"].id
  secret_data = random_password.secret_key.result
}

resource "random_password" "webhook_secret" {
  length = 32
}

resource "google_secret_manager_secret_version" "webhook_secret" {
  secret      = google_secret_manager_secret.secrets["telegram-webhook-secret"].id
  secret_data = random_password.webhook_secret.result
}

# IAM for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "${var.environment}-appointment-bot-run"
  display_name = "Appointment Bot Cloud Run Service Account"
}

resource "google_project_iam_member" "cloud_run_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Build trigger (optional)
resource "google_cloudbuild_trigger" "main" {
  name        = "${var.environment}-appointment-bot-trigger"
  description = "Trigger for appointment bot deployment"

  github {
    owner = "your-github-username"  # Update this
    name  = "appointment-bot"       # Update this
    push {
      branch = var.environment == "prod" ? "main" : "develop"
    }
  }

  filename = "deployment/gcp/cloudbuild.yml"

  substitutions = {
    _REGION        = var.region
    _VPC_CONNECTOR = google_vpc_access_connector.connector.name
  }

  depends_on = [google_project_service.apis]
}

# Outputs
output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "vpc_name" {
  value = google_compute_network.vpc.name
}

output "vpc_connector_name" {
  value = google_vpc_access_connector.connector.name
}

output "postgres_instance_name" {
  value = google_sql_database_instance.postgres.name
}

output "postgres_private_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}

output "redis_host" {
  value = google_redis_instance.redis.host
}

output "cloud_run_service_account" {
  value = google_service_account.cloud_run.email
}

output "secrets_to_set_manually" {
  value = [
    "neo4j-uri",
    "neo4j-password", 
    "openai-api-key",
    "anthropic-api-key",
    "telegram-bot-token",
    "pinecone-api-key"
  ]
  description = "These secrets need to be set manually in Secret Manager"
}