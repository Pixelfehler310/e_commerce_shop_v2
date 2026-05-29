# Systemarchitektur und Kommunikation

## Architekturüberblick

Die Systemlandschaft besteht aus fünf Backend-Services, mehreren Datenhaltungen, einer Message Queue und vier Frontends. Die Services sind fachlich getrennt und besitzen jeweils eigene technische Verantwortung.

```text
Frontends
  |-- Customer Storefront
  |-- Admin Dashboard
  |-- Warehouse WMS
  |-- Simulation Panel
        |
        v
Shop-Service als Gateway und Saga-Orchestrator
  |-- synchron REST --> Warehouse-Service
  |-- synchron REST --> Billing-Service
  |-- Domain Events --> RabbitMQ --> Audit-Service
                           |------> Invoice-Service
```

## Service-Landkarte

| Service | Fachliche Verantwortung | Persistenz | Externe Sichtbarkeit |
| --- | --- | --- | --- |
| Shop-Service | Gateway, Auth, Rollen, Produktkatalog, Warenkorb, Bestellung, Saga-Orchestrierung | PostgreSQL, Redis | Öffentlich für Frontends |
| Warehouse-Service | Bestand, Reservierung, Ausbuchung, Wareneingang, Fehlerprovokation | PostgreSQL | Intern, über Shop erreichbar |
| Billing-Service | Payment-Fassade, Charges, Refunds, Webhooks, Zahlungsstatus | PostgreSQL | Intern, Webhook-Endpunkt kontrolliert erreichbar |
| Invoice-Service | PDF-Rechnungserstellung nach Zahlungserfolg | Dateisystem oder Volume | Nicht öffentlich |
| Audit-Service | Append-only Snapshots, Audit-Historie, Stream für Dashboard | PostgreSQL | Lesbar über Admin-Kontext |

## Kommunikationsregeln

Die Kommunikation folgt festen Regeln, damit Kopplung sichtbar und kontrollierbar bleibt:

- Frontends sprechen ausschließlich den Shop-Service an, außer wenn ein internes Admin- oder Monitoring-Proxy explizit über den Shop-Service bereitgestellt wird.
- Der Shop-Service ruft Warehouse und Billing synchron auf, weil der Benutzer während der Bestellung ein direktes Ergebnis benötigt.
- Billing publiziert nach erfolgreicher Zahlung ein `PaymentSucceeded`-Event an RabbitMQ.
- Invoice verarbeitet Rechnungen asynchron, damit Rechnungsfehler nicht automatisch die Zahlung rückgängig machen.
- Alle Services publizieren Domain-Events oder Audit-Snapshots an den Audit-Service.
- Kein Service liest oder schreibt in die Datenbank eines anderen Services.

## Synchrone Kommunikation

Synchrone REST-Kommunikation wird dort eingesetzt, wo der aufrufende Prozess das Ergebnis unmittelbar für die nächste Entscheidung benötigt.

| Aufrufer | Ziel | Zweck | Erwartung |
| --- | --- | --- | --- |
| Shop-Service | Warehouse-Service | Bestand reservieren | Sofortige Zusage oder Ablehnung. |
| Shop-Service | Billing-Service | Zahlung starten | Sofortiger Erfolg, Fehler oder Pending-Status. |
| Shop-Service | Warehouse-Service | Reservierung stornieren | Kompensation nach Zahlungsfehler. |
| Shop-Service | Warehouse-Service | Bestand final ausbuchen | Abschluss nach Zahlungserfolg. |
| Shop-Service | Billing-Service | Refund auslösen | Kompensation nach Booking-Fehler. |

## Asynchrone Kommunikation

Asynchrone Events werden für entkoppelte Folgeprozesse verwendet.

| Event | Publisher | Consumer | Zweck |
| --- | --- | --- | --- |
| `PaymentSucceeded` | Billing-Service | Invoice-Service, Audit-Service | Rechnungserstellung und Audit. |
| `PaymentFailed` | Billing-Service | Audit-Service | Zahlungsfehler dokumentieren. |
| `OrderStatusChanged` | Shop-Service | Audit-Service | Bestellstatus nachvollziehbar machen. |
| `ReservationCreated` | Warehouse-Service | Audit-Service | Bestandssperre dokumentieren. |
| `ReservationCancelled` | Warehouse-Service | Audit-Service | Kompensation dokumentieren. |
| `StockBooked` | Warehouse-Service | Audit-Service | Finalen Lagerabgang dokumentieren. |
| `CircuitBreakerStateChanged` | Invoice-Service | Audit-Service | Resilienzverhalten sichtbar machen. |

## Header-Konventionen

Jeder Service muss technische Kontextinformationen weiterreichen:

| Header | Pflicht | Bedeutung |
| --- | --- | --- |
| `X-Correlation-Id` | Ja | Verbindet Logs, Audit-Einträge und Service-Aufrufe. |
| `X-Idempotency-Key` | Für `POST /v1/orders` | Verhindert doppelte Bestellausführung. |
| `Authorization` | Für geschützte Endpunkte | JWT mit Rolle und User-ID. |
| `Content-Type` | Ja | `application/json` für APIs, `application/problem+json` für Fehler. |

## Fehlerformat nach RFC 7807

Fehlerantworten folgen einem einheitlichen Schema:

```json
{
  "type": "https://example.local/problems/out-of-stock",
  "title": "Insufficient stock",
  "status": 409,
  "detail": "Product is not available in the requested quantity.",
  "instance": "/v1/orders/9f4c...",
  "correlationId": "9f4c...",
  "code": "OUT_OF_STOCK"
}
```

## Datenhoheit

Jeder Service ist Eigentümer seiner Daten:

- Shop-Service besitzt Produkte, Warenkörbe, Bestellungen, Nutzer und Rollen aus Sicht des Shop-Kerns.
- Warehouse-Service besitzt physische Bestände, Reservierungen und Buchungen.
- Billing-Service besitzt Zahlungsversuche, Anbieterreferenzen, Refunds und Webhook-Zustände.
- Invoice-Service besitzt Rechnungsdateien und Generierungsstatus.
- Audit-Service besitzt ausschließlich unveränderliche Snapshots.

## Konsistenzmodell

Das System arbeitet bewusst mit eventual consistency zwischen Services. Lokale Transaktionen sind pro Service möglich, aber es gibt keine globale Datenbanktransaktion. Die Konsistenz entsteht durch:

- Klar definierte Saga-Schritte.
- Kompensationsendpunkte.
- Statusmodelle mit Endzuständen.
- Idempotente Wiederholung kritischer Befehle.
- Auditierbare Ereigniskette.
- Kontrollierte Retry- und Circuit-Breaker-Mechanismen.

## Sicherheitsgrenzen

Der Shop-Service validiert externe Anfragen, Rollen und Tokens. Interne Service-Kommunikation sollte ebenfalls abgesichert werden, mindestens durch Netzwerkisolation in Docker Compose und optional durch interne Shared Secrets oder Service Tokens.

Empfohlene Mindestregeln:

- Nur der Shop-Service veröffentlicht externe Ports für Business-APIs.
- RabbitMQ Management UI und Datenbanken sind nur lokal oder intern erreichbar.
- Simulation-Endpunkte sind nur für `ADMIN` freigegeben.
- Warehouse-Bestandsänderungen sind nur für `LOGISTICS` oder `ADMIN` erlaubt.

## Technologiestack

| Bereich | Technologie |
| --- | --- |
| Runtime | Node.js |
| Sprache | TypeScript |
| Backend Framework | NestJS |
| Datenbank | PostgreSQL |
| Cache | Redis |
| Message Broker | RabbitMQ |
| Frontend | React |
| Logging | JSON-Logs, Loki |
| Dashboard | Grafana |
| Deployment | Docker Compose |