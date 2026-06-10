# Keepalived для отказоустойчивой точки входа

В локальном Minikube на macOS Keepalived с VRRP/VIP обычно нельзя полноценно
проверить: для VRRP нужна L2-сеть между Linux-нодами и возможность назначать
виртуальный IP на сетевой интерфейс.

Поэтому в локальном кластере используется `edge-haproxy` как NodePort-сервис.
Для production/bare-metal можно поставить HAProxy на две внешние edge-ноды и
поднять между ними Keepalived.

## Схема

```text
client
  |
  v
VIP 192.168.10.100
  |
  +-- edge-1: HAProxy + Keepalived MASTER
  |
  +-- edge-2: HAProxy + Keepalived BACKUP
  |
  v
Kubernetes NodePort / Istio ingressgateway
```

## Проверка Keepalived

На активной edge-ноде:

```bash
ip addr show
systemctl status keepalived
```

При остановке MASTER:

```bash
sudo systemctl stop keepalived
```

VIP должен перейти на BACKUP-ноду.
