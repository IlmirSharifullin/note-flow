locals {
  namespaces = {
    argocd = {
      name = "argocd"
      labels = {
        "app.kubernetes.io/part-of" = "gitops"
      }
    }
    noteflow = {
      name = "noteflow"
      labels = {
        "app.kubernetes.io/part-of" = "noteflow"
      }
    }
    kafka = {
      name = "kafka"
      labels = {
        "app.kubernetes.io/part-of" = "messaging"
      }
    }
    monitoring = {
      name = "monitoring"
      labels = {
        "app.kubernetes.io/part-of" = "observability"
      }
    }
  }

  service_accounts = {
    noteflow_app = {
      name      = "noteflow-app"
      namespace = "noteflow"
    }
    noteflow_deployer = {
      name      = "noteflow-deployer"
      namespace = "noteflow"
    }
    kafka_deployer = {
      name      = "kafka-deployer"
      namespace = "kafka"
    }
  }
}

resource "kubernetes_namespace_v1" "this" {
  for_each = local.namespaces

  metadata {
    name   = each.value.name
    labels = each.value.labels
  }
}

resource "kubernetes_service_account_v1" "this" {
  for_each = local.service_accounts

  metadata {
    name      = each.value.name
    namespace = each.value.namespace
  }

  depends_on = [
    kubernetes_namespace_v1.this,
  ]
}

resource "kubernetes_secret_v1" "noteflow_base" {
  metadata {
    name      = "noteflow-base-secrets"
    namespace = kubernetes_namespace_v1.this["noteflow"].metadata[0].name
  }

  type = "Opaque"

  data = {
    JWT_SECRET            = var.jwt_secret
    POSTGRES_PASSWORD     = var.postgres_password
    MINIO_ROOT_USER       = var.minio_root_user
    MINIO_ROOT_PASSWORD   = var.minio_root_password
    REDIS_PASSWORD        = var.redis_password
    KAFKA_BOOTSTRAP_HOSTS = var.kafka_bootstrap_hosts
  }
}

resource "kubernetes_secret_v1" "kafka_client" {
  metadata {
    name      = "noteflow-kafka-client"
    namespace = kubernetes_namespace_v1.this["kafka"].metadata[0].name
  }

  type = "Opaque"

  data = {
    username = var.kafka_client_username
    password = var.kafka_client_password
  }
}
