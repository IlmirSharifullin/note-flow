output "namespaces" {
  description = "Created Kubernetes namespaces."
  value       = { for key, ns in kubernetes_namespace_v1.this : key => ns.metadata[0].name }
}

output "service_accounts" {
  description = "Created Kubernetes service accounts."
  value = {
    for key, sa in kubernetes_service_account_v1.this :
    key => "${sa.metadata[0].namespace}/${sa.metadata[0].name}"
  }
}
