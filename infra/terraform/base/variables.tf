variable "kubeconfig_path" {
  description = "Path to kubeconfig file."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context used by Terraform."
  type        = string
  default     = "noteflow-cilium"
}

variable "jwt_secret" {
  description = "JWT signing secret for NoteFlow services."
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "Default PostgreSQL password for local NoteFlow infrastructure."
  type        = string
  sensitive   = true
}

variable "minio_root_user" {
  description = "MinIO root username."
  type        = string
  sensitive   = true
}

variable "minio_root_password" {
  description = "MinIO root password."
  type        = string
  sensitive   = true
}

variable "redis_password" {
  description = "Redis password for environments where Redis auth is enabled."
  type        = string
  sensitive   = true
}

variable "kafka_bootstrap_hosts" {
  description = "Kafka bootstrap address used by NoteFlow services."
  type        = string
}

variable "kafka_client_username" {
  description = "Kafka client username."
  type        = string
  default     = "noteflow"
}

variable "kafka_client_password" {
  description = "Kafka client password."
  type        = string
  sensitive   = true
}
