# Infrastruktur, Deployment und Repository-Struktur

## Zielbild

Alle Bestandteile des Systems sollen lokal reproduzierbar über Docker Compose startbar sein. Die Infrastruktur bildet nicht nur Datenbanken und Broker ab, sondern auch Redis, Frontends und Observability. Konfiguration erfolgt ausschließlich über Umgebungsvariablen.

## Container-Landkarte

| Container | Zweck | Abhängigkeiten |
| --- | --- | --- |
| `shop-service` | Gateway, IAM, Katalog, Warenkorb, Saga | `shop-db`, `redis`, `rabbitmq`, Warehouse, Billing |
| `warehouse-service` | Bestand, Reservierung, Booking | `warehouse-db`, `rabbitmq` |
| `billing-service` | Payment-Fassade, Webhooks, Refunds | `billing-db`, `rabbitmq` |
| `invoice-service` | PDF-Rechnungserstellung | `rabbitmq`, Invoice-Volume |
| `audit-service` | Append-only Snapshots, Stream | `audit-db`, `rabbitmq` |
| `shop-db` | Shop-PostgreSQL | Volume |
| `warehouse-db` | Warehouse-PostgreSQL | Volume |
| `billing-db` | Billing-PostgreSQL | Volume |
| `audit-db` | Audit-PostgreSQL | Volume |
| `redis` | Idempotenz und Sessions | Volume optional |
| `rabbitmq` | Message Broker | Management UI optional |
| `loki` | Logspeicher | Volume |
| `grafana` | Dashboards | Loki |
| `storefront-ui` | Customer Frontend | Shop-Service |
| `admin-dashboard` | Admin Frontend | Shop-Service |
| `warehouse-wms` | Warehouse Frontend | Shop-Service |
| `simulation-panel` | Demo Control Panel | Shop-Service |

## Docker-Compose-Prinzipien

- Jeder Service erhält einen eindeutigen Container-Namen.
- Datenbanken laufen in eigenen Containern, nicht als geteilte Instanz mit gemeinsamen Schemas.
- Services kommunizieren über interne Docker-DNS-Namen.
- Nur notwendige Ports werden auf den Host veröffentlicht.
- Healthchecks verhindern, dass abhängige Services zu früh starten.
- Volumes sichern Datenbank- und Rechnungsdaten.
- `.env` steuert Ports, Secrets, Provider-Auswahl und Simulation.

## Netzwerkstruktur

Empfohlen sind zwei Docker-Netzwerke:

| Netzwerk | Enthält | Zweck |
| --- | --- | --- |
| `public-net` | Frontends, Shop-Service | Zugriff vom Browser auf Gateway und UIs. |
| `internal-net` | Services, Datenbanken, Redis, RabbitMQ | Interne Service-Kommunikation. |

Nur der Shop-Service hängt an beiden Netzwerken. Interne Services bleiben im `internal-net`.

## Ports

Beispielhafte lokale Ports:

| Komponente | Host-Port | Intern |
| --- | --- | --- |
| Shop-Service | `3000` | `3000` |
| Storefront UI | `5173` | `5173` |
| Admin Dashboard | `5174` | `5173` |
| Warehouse WMS | `5175` | `5173` |
| Simulation Panel | `5176` | `5173` |
| RabbitMQ Management | `15672` | `15672` |
| Grafana | `3001` | `3000` |
| Loki | nicht öffentlich nötig | `3100` |

## Umgebungsvariablen

### Allgemein

```env
NODE_ENV=development
LOG_LEVEL=info
JWT_SECRET=change-me-local
RABBITMQ_URL=amqp://app:app@rabbitmq:5672
REDIS_URL=redis://redis:6379
```

### Shop-Service

```env
SHOP_DATABASE_URL=postgres://shop:shop@shop-db:5432/shop
WAREHOUSE_BASE_URL=http://warehouse-service:3000
BILLING_BASE_URL=http://billing-service:3000
AUDIT_EVENTS_EXCHANGE=audit.domain-events
IDEMPOTENCY_TTL_SECONDS=86400
```

### Warehouse-Service

```env
WAREHOUSE_DATABASE_URL=postgres://warehouse:warehouse@warehouse-db:5432/warehouse
WAREHOUSE_LOCK_TIMEOUT_MS=5000
WAREHOUSE_DEFAULT_RESERVATION_TTL_SECONDS=900
```

### Billing-Service

```env
BILLING_DATABASE_URL=postgres://billing:billing@billing-db:5432/billing
PAYMENT_PROVIDER=stripe-sim
PAYMENT_WEBHOOK_DELAY_MS=2500
PAYMENT_WEBHOOK_SECRET=change-me-local
```

### Invoice-Service

```env
INVOICE_OUTPUT_DIR=/data/invoices
INVOICE_RETRY_ATTEMPTS=3
INVOICE_CIRCUIT_BREAKER_FAILURES=3
INVOICE_CIRCUIT_BREAKER_OPEN_MS=30000
```

### Audit-Service

```env
AUDIT_DATABASE_URL=postgres://audit:audit@audit-db:5432/audit
AUDIT_STREAM_HEARTBEAT_MS=15000
```

## Healthchecks

Jeder Service bietet:

```http
GET /health
```

Antwort:

```json
{
  "status": "ok",
  "service": "shop-service",
  "dependencies": {
    "database": "ok",
    "redis": "ok",
    "rabbitmq": "ok"
  }
}
```

Healthchecks sollten technische Bereitschaft prüfen, aber nicht zu teuer sein.

## Migrationen und Seed-Daten

Jeder Service verwaltet eigene Migrationen. Ein zentrales Migrationsskript darf die Services nacheinander starten, aber nicht gemeinsame Schemas erzeugen.

Seed-Daten für Demo:

- Admin-Nutzer.
- Logistics-Nutzer.
- Customer-Nutzer.
- Drei bis fünf Produkte.
- Ein Produkt mit Bestand `1` für Concurrency-Test.
- Ein Produkt mit ausreichend Bestand für Happy Path.

## Repository-Struktur

```text
/
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── demo-script.md
│   └── decisions/
│       ├── 001-service-boundaries.md
│       ├── 002-saga-orchestration.md
│       ├── 003-payment-facade.md
│       └── 004-observability-stack.md
├── konzept/
├── shop-service/
├── warehouse-service/
├── billing-service/
├── invoice-service/
├── audit-service/
└── frontends/
    ├── storefront-ui/
    ├── admin-dashboard/
    ├── warehouse-wms/
    └── simulation-panel/
```

## Service-interne Struktur

Für NestJS-Services empfiehlt sich:

```text
src/
├── app.module.ts
├── main.ts
├── config/
├── common/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── logging/
├── modules/
│   └── <domain>/
│       ├── controllers/
│       ├── application/
│       ├── domain/
│       ├── infrastructure/
│       └── dto/
└── migrations/
```

## ADRs

Mindestens folgende Architecture Decision Records sollten erstellt werden:

| ADR | Entscheidung |
| --- | --- |
| `001-service-boundaries` | Warum genau diese fünf Services. |
| `002-database-per-service` | Warum keine gemeinsame Datenbank. |
| `003-saga-orchestration` | Warum Shop-Service orchestriert. |
| `004-rabbitmq-events` | Warum RabbitMQ für asynchrone Verarbeitung. |
| `005-payment-facade` | Warum Provider-Fassade statt direkter Stubs. |
| `006-pessimistic-locking` | Warum Warehouse `SELECT ... FOR UPDATE` nutzt. |
| `007-observability` | Warum Loki/Grafana und JSON-Logs. |

## Skalierung

Im Docker-Compose-Kontext kann der Warehouse-Service horizontal skaliert werden, um zu zeigen, dass Concurrency nicht im Prozessspeicher, sondern in der Datenbank abgesichert wird.

Beispielziel:

```text
docker compose up --scale warehouse-service=2
```

Wichtig: Der Concurrency-Test muss auch bei mehreren Warehouse-Instanzen korrekt bleiben, weil PostgreSQL die Sperre zentral hält.

## Lokaler Startablauf

Empfohlene Kommandoreihenfolge in der späteren Implementierung:

```text
cp .env.example .env
docker compose build
docker compose up -d postgres/rabbitmq/redis
docker compose run --rm shop-service npm run migration:run
docker compose run --rm warehouse-service npm run migration:run
docker compose run --rm billing-service npm run migration:run
docker compose run --rm audit-service npm run migration:run
docker compose run --rm shop-service npm run seed
docker compose up
```

Die tatsächlichen Kommandos hängen vom finalen Package-Setup ab, sollten aber in `docs/demo-script.md` eindeutig dokumentiert werden.

## Abnahmekriterien

- `docker compose up` startet alle Pflichtservices.
- Jeder Service hat eigene Konfiguration und eigene Datenhaltung.
- RabbitMQ, Redis und Datenbanken sind intern erreichbar.
- Frontends sind lokal auf dokumentierten Ports erreichbar.
- Grafana zeigt Logs aus mehreren Services.
- `.env.example` enthält alle benötigten Variablen ohne echte Secrets.