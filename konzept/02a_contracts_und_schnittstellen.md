# Contracts und Schnittstellenkatalog

## Zweck dieses Kapitels

Dieses Kapitel buendelt die aktuell definierten Contracts an einer Stelle. Es soll nicht die service-spezifischen Kapitel ersetzen, sondern die Stellen zusammenziehen, die spaeter am haeufigsten nachgeschaerft werden muessen: Routen, Header, Payload-Zuschnitte, Event-Namen und technische Anker im Code.

Wichtig fuer den Ist-Stand: Die meisten Business-Endpunkte sind im Code bereits als Controller- oder Event-Stub angelegt, fuehren aber technisch noch `request: unknown` und werfen `NotImplementedException("Contract stub only")`. Genau deshalb ist diese Seite der zentrale Editierpunkt, solange DTOs, Interfaces und Contract-Tests noch nachgezogen werden.

## Pflege-Regel bei Contract-Aenderungen

Wenn sich ein Contract aendert, sollten immer dieselben vier Ebenen gemeinsam angepasst werden:

1. Technischer Anker im Controller oder Event-Consumer.
2. Dieses Kapitel als zentrale Uebersicht.
3. Das betroffene Service-Kapitel, zum Beispiel [Shop-Service](03_service_shop.md) oder [Billing und Invoice](05_service_billing_invoice.md).
4. Contract-Tests, OpenAPI/AsyncAPI-Spezifikation und Demo-/Abnahmeszenarien.

Die Health-Endpunkte sind davon ausgenommen. Sie sind bereits technisch implementiert und dienen eher dem Betrieb als dem fachlichen Contract.

## Contract-Landkarte

| Contract-Flaeche | Producer/Owner | Consumer | Technischer Anker im Code | Ist-Stand |
| --- | --- | --- | --- | --- |
| Oeffentliche Shop-REST-API | Shop-Service | Frontends, Admin, Demo | `shop-service/src/modules/auth/controllers/auth.controller.ts`, `.../products.controller.ts`, `.../basket.controller.ts`, `.../orders.controller.ts`, `.../admin.controller.ts`, `.../me.controller.ts` | Routen stehen, Payload-Typisierung ist noch offen. |
| Interne Warehouse-REST-API | Warehouse-Service | Shop-Service, `LOGISTICS`, `ADMIN` | `warehouse-service/src/modules/products/controllers/warehouse-products.controller.ts`, `.../reservations.controller.ts`, `.../bookings.controller.ts`, `.../simulation.controller.ts` | Routen stehen, fachliche Request-/Response-Schemas sind im Konzept beschrieben. |
| Interne Billing-REST-API | Billing-Service | Shop-Service, Payment-Stub, `ADMIN` | `billing-service/src/modules/charges/controllers/billing-charges.controller.ts`, `.../refunds.controller.ts`, `.../webhooks.controller.ts`, `.../simulation.controller.ts` | Routen stehen, Charge-/Refund-/Webhook-Payloads sind teilweise bereits fachlich konkretisiert. |
| Audit REST und SSE | Audit-Service | Interne Services, Admin Dashboard | `audit-service/src/modules/snapshots/controllers/audit-snapshots.controller.ts`, `.../orders.controller.ts`, `.../search.controller.ts`, `.../stream.controller.ts` | Snapshot-Write, Search, Timeline und Stream sind als Contracts angelegt. |
| Async Event-Consumer | Invoice-Service, Audit-Service | Billing, Shop, Warehouse, Invoice | `invoice-service/src/modules/events/controllers/invoice-events.controller.ts`, `audit-service/src/modules/events/controllers/audit-events.controller.ts` | Event-Einstiegspunkte stehen, Event-Payloads muessen als versionierte Schemas gepflegt werden. |
| Health und Betriebs-Checks | Alle Services | Compose, Admin, Betrieb | `*/src/common/health/health.controller.ts`, `shop-service/src/modules/admin/controllers/service-health.controller.ts` | Technisch bereits implementiert. |

## Oeffentliche REST-Contracts des Shop-Service

Detailtiefe und fachliche Hintergruende stehen in [Shop-Service](03_service_shop.md). Diese Tabelle ist der schnelle Einstieg fuer die konkrete API-Oberflaeche.

### Authentisierung und Benutzerkontext

| Methode | Pfad | Kern-Request | Kern-Response | Besondere Regeln |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/auth/register` | `email`, `password`, `displayName` | angelegter Nutzer oder leere Success-Response | Standardrolle `CUSTOMER`. |
| `POST` | `/v1/auth/login` | Credentials | `accessToken`, `tokenType`, `expiresIn`, `user` | JWT ist Basis fuer alle geschuetzten Endpunkte. |
| `GET` | `/v1/me` | kein Body | aktueller Benutzerkontext | Dient Frontends als Session-/Profil-Read-Modell. |

### Katalog, Warenkorb und Bestellung

| Methode | Pfad | Kern-Request | Kern-Response | Besondere Regeln |
| --- | --- | --- | --- | --- |
| `GET` | `/v1/products` | Query fuer Paging/Filter | paginierte Produktliste | Customer sieht nur aktive Produkte, Admin optional alle. |
| `GET` | `/v1/products/{productId}` | `productId` als Pfadparameter | Produktdetail | Produkt-ID ist Shop-weite Referenz und wird an Warehouse weitergereicht. |
| `POST` | `/v1/products` | `name`, `description`, `priceGross`, `currency`, `sku`, `initialStock`, `active` | angelegtes Produkt | Initialisiert synchron den Warehouse-Bestand. |
| `PATCH` | `/v1/products/{productId}` | partielle Produktaenderung | aktualisiertes Produkt | Aenderung betrifft nur Shop-Sicht, nicht vergangene Order-Snapshots. |
| `GET` | `/v1/baskets` | kein Body | aktiver Warenkorb | Basis fuer Checkout; Preise werden spaeter in die Order kopiert. |
| `POST` | `/v1/baskets/items` | mindestens `productId`, `quantity` | aktualisierter Warenkorb oder Position | Fuegt hinzu oder erhoeht Menge. |
| `PATCH` | `/v1/baskets/items/{productId}` | mindestens `quantity` | aktualisierte Position | Nur positive Ganzzahlen zulassen. |
| `DELETE` | `/v1/baskets/items/{productId}` | kein Body | fachlich idempotente Entfernen-Response | Wiederholtes Entfernen darf nicht fachlich eskalieren. |
| `POST` | `/v1/orders` | Checkout-Body noch nicht finalisiert; fachlich zwingend sind `X-Idempotency-Key` und optional `X-Correlation-Id` | Order-Status oder gespeicherte Idempotenz-Antwort | Warenkorb ist die Bestellbasis, nicht ein frei zusammengesetzter Item-Body. |
| `GET` | `/v1/orders` | Query fuer Status, Paging, Rolle | eigene oder administrative Orderliste | CUSTOMER nur eigene Bestellungen. |
| `GET` | `/v1/orders/{correlationId}` | `correlationId` | Status, Prozess- und Referenzinformationen | `correlationId` ist fachlicher Leitanker fuer Logs, Audit und Servicegrenzen. |

Pflichtheader fuer den Checkout:

```http
Authorization: Bearer <jwt>
X-Idempotency-Key: <client-generated-key>
X-Correlation-Id: <optional-client-correlation-id>
```

### Admin, Demo und Betriebszugriff

| Methode | Pfad | Zweck | Contract-Hinweis |
| --- | --- | --- | --- |
| `GET` | `/v1/admin/orders` | administrative Ordersuche | Muss Filter auf Status, Zeitraum und `correlationId` tragen koennen. |
| `GET` | `/v1/admin/orders/{correlationId}/timeline` | zusammengezogene Timeline fuer Admin | Kann Audit-Read-Model oder Shop-Proxy sein, aber die Antwort bleibt Admin-zentriert. |
| `GET` | `/v1/admin/audit/stream` | Live-Stream ins Dashboard | Transportiert SSE oder Proxy-SSE in den Admin-Kontext. |
| `POST` | `/v1/admin/simulation/{scenario}` | Demo-Szenarien triggern | Darf nur kontrollierte Fehlerpfade freischalten. |
| `GET` | `/v1/admin/health/services` | Uebersicht aller Service-Healthchecks | Technisch bereits implementiert; dient als betrieblicher Contract. |

## Interne REST-Contracts

### Shop-Service zu Warehouse-Service

Detailtiefe und Invarianten stehen in [Warehouse-Service](04_service_warehouse.md).

| Methode | Pfad | Zweck | Kernfelder | Regeln |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/warehouse/products` | Bestand zu neuem Produkt anlegen | `productId`, `sku`, `initialStock` | Muss im Erfolgsfall genau einen Warehouse-Datensatz anlegen. |
| `PATCH` | `/v1/warehouse/products/{productId}/stock` | Wareneingang oder Korrektur | `quantityDelta`, `reason`, `reference` | Negative Deltas nur kontrolliert und nie unter `0`. |
| `GET` | `/v1/warehouse/products/{productId}/stock` | Bestandsansicht lesen | `productId` | Antwort muss freien, reservierten und gebuchten Bestand trennen. |
| `POST` | `/v1/warehouse/reservations` | Bestand pruefen und reservieren | `correlationId`, `items[]` mit `productId`, `quantity` | Idempotent pro `correlationId`; verwendet pessimistische Sperren. |
| `DELETE` | `/v1/warehouse/reservations/{correlationId}` | Reservierung stornieren | `correlationId` im Pfad | Zweiter Storno darf Mengen nicht erneut freigeben. |
| `POST` | `/v1/warehouse/bookings` | Reservierte Ware final buchen | mindestens `correlationId` oder eindeutige Reservierungsreferenz | Nur fuer aktive Reservierungen; idempotent. |
| `POST` | `/v1/warehouse/simulation/failure-mode` | Fehler oder Delay setzen | Modus und Wirkungsdauer/Einmaligkeit | Ausschliesslich fuer `ADMIN` bzw. Demo-Kontext. |

Kanonischer Reservierungs-Request:

```json
{
  "correlationId": "ord-2026-0001",
  "items": [
    { "productId": "prd-1", "quantity": 1 },
    { "productId": "prd-2", "quantity": 2 }
  ]
}
```

Kanonischer Bestands-Adjust-Request:

```json
{
  "quantityDelta": 15,
  "reason": "INBOUND_DELIVERY",
  "reference": "DEL-2026-05-29-001"
}
```

### Shop-Service zu Billing-Service

Detailtiefe steht in [Billing und Invoice](05_service_billing_invoice.md).

| Methode | Pfad | Zweck | Kernfelder | Regeln |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/billing/charges` | Zahlung starten | `correlationId`, `amountGross`, `currency`, `customerId`, `paymentMethod` | Ergebnis muss `SUCCEEDED`, `FAILED` oder `PENDING` kanonisch abbilden. |
| `GET` | `/v1/billing/charges/{correlationId}` | Payment-Status abfragen | `correlationId` | Wichtig fuer Pending-Fortsetzung und Admin-Read-Model. |
| `POST` | `/v1/billing/refunds` | Rueckerstattung ausloesen | mindestens `correlationId`, optional fachliche Begruendung | Nur nach erfolgreicher Zahlung; idempotent. |
| `POST` | `/v1/billing/webhooks/{provider}` | asynchrones Provider-Callback | provider-spezifische Felder | Provider-spezifisch im Eingang, intern auf Billing-Statusmodell mappen. |
| `POST` | `/v1/billing/simulation/provider-mode` | Demo-Modus setzen | Provider-/Mode-Konfiguration | Nur fuer `ADMIN`; bestimmt den naechsten Payment-Ausgang. |

Kanonischer Charge-Request:

```json
{
  "correlationId": "ord-2026-0001",
  "amountGross": 259.98,
  "currency": "EUR",
  "customerId": "usr-123",
  "paymentMethod": {
    "type": "SIMULATED_CARD",
    "token": "tok_demo_success"
  }
}
```

Kanonische Charge-Response:

```json
{
  "correlationId": "ord-2026-0001",
  "paymentId": "pay-123",
  "provider": "stripe-sim",
  "providerTransactionId": "txn_abc",
  "status": "SUCCEEDED"
}
```

Asynchroner Erfolgsfall ueber denselben Contract:

```json
{
  "correlationId": "ord-2026-0001",
  "paymentId": "pay-123",
  "provider": "async-webhook-sim",
  "providerTransactionId": "txn_async_abc",
  "status": "PENDING"
}
```

### Services zu Audit-Service

Detailtiefe steht in [Audit-Service](06_audit_service.md).

| Methode | Pfad | Zweck | Kernfelder | Regeln |
| --- | --- | --- | --- | --- |
| `POST` | `/v1/audit/snapshots` | Snapshot anhaengen | `correlationId`, `eventType`, `sourceService`, `timestamp`, `payload`, `metadata` | Append-only; keine spaeteren Updates oder Deletes. |
| `GET` | `/v1/audit/orders/{correlationId}` | Timeline laden | `correlationId` | Chronologische Reihenfolge und vollstaendige Kette. |
| `GET` | `/v1/audit/search` | Snapshots filtern | Query zu Typ, Service, Zeitraum, Status | Read-Model fuer Admin und Debugging. |
| `GET` | `/v1/audit/stream` | Snapshots live streamen | Query z. B. fuer `correlationId` | Liefert SSE mit Heartbeats und Reconnect-Faehigkeit. |

Kanonisches Snapshot-Schema:

```json
{
  "id": "evt-123",
  "correlationId": "ord-2026-0001",
  "eventType": "PaymentSucceeded",
  "sourceService": "billing-service",
  "timestamp": "2026-05-29T12:00:00.000Z",
  "previousEventId": "evt-122",
  "payload": {
    "paymentId": "pay-123",
    "provider": "stripe-sim",
    "amountGross": 259.98,
    "currency": "EUR"
  },
  "metadata": {
    "schemaVersion": 1,
    "traceId": "trace-abc",
    "spanId": "span-def"
  }
}
```

SSE-Beispiel fuer den Stream:

```text
event: audit.snapshot
id: evt-123
data: {"correlationId":"ord-2026-0001","eventType":"PaymentSucceeded"}
```

## Asynchrone Event-Contracts

Die REST-Endpunkte sind nicht die einzige Contract-Flaeche. Fuer das System entscheidend sind auch Broker-Events und ihre fachlichen Feldzuschnitte.

| Technischer Kanal | Fachlicher Eventtyp | Producer | Consumer | Pflichtfelder |
| --- | --- | --- | --- | --- |
| `PaymentSucceeded` | erfolgreicher Zahlungsabschluss | Billing-Service | Invoice-Service | `correlationId`, `orderId`, `paymentId`, `amount`, `currency`, `timestamp` |
| `audit.domain-events` | normalisierte Domain- und Audit-Events | Shop-, Warehouse-, Billing-, Invoice-Service | Audit-Service | `correlationId`, `eventType`, `sourceService`, `timestamp`, `payload`, `metadata` |
| `GET /v1/audit/stream` als SSE | Live-Snapshot fuer Admin | Audit-Service | Admin Dashboard | `id`, `eventType`, `correlationId`, kompakter Status-/Payload-Ausschnitt |

Wichtige fachliche Eventtypen, die in Payloads oder Snapshots konsistent bleiben muessen:

| Quelle | Fachliche Eventtypen |
| --- | --- |
| Shop | `OrderCreated`, `OrderReservationRequested`, `OrderPaymentRequested`, `OrderPaymentPending`, `OrderCompleted`, `OrderFailedOutOfStock`, `OrderFailedPayment`, `OrderRollbackStarted`, `OrderRollbackCompleted` |
| Warehouse | `WarehouseProductInitialized`, `StockAdjusted`, `ReservationCreated`, `ReservationRejected`, `ReservationCancelled`, `StockBooked`, `WarehouseFailureInjected` |
| Billing | `PaymentInitiated`, `PaymentProviderRequested`, `PaymentPending`, `PaymentSucceeded`, `PaymentFailed`, `PaymentRefundRequested`, `PaymentRefunded`, `PaymentRefundFailed`, `PaymentWebhookReceived` |
| Invoice | `InvoiceGenerationRequested`, `InvoiceGenerated`, `InvoiceGenerationFailed`, `InvoiceRetryScheduled`, `CircuitBreakerStateChanged` |

## Offene Stellen fuer die weitere Bearbeitung

Die folgenden Punkte sind bewusst noch nicht final und sollten spaeter als DTOs, Interfaces oder Schemas nachgeschaerft werden:

- Die Controller-Bodies sind im Code fast ueberall noch `unknown`; die Route steht also, das Request-/Response-Typmodell noch nicht.
- `POST /v1/orders` ist fachlich ueber Warenkorb plus Header definiert, aber noch nicht als finaler Checkout-Body typisiert.
- `POST /v1/warehouse/bookings` und `POST /v1/billing/refunds` sind semantisch klar ueber `correlationId`, aber das konkrete DTO-Shape ist noch offen.
- `POST /v1/billing/webhooks/{provider}` bleibt provider-spezifisch im Eingang und muss intern auf kanonische Billing-Events gemappt werden.
- Beim Audit gibt es zwei Ebenen, die konsistent gehalten werden muessen: technischer Transport (`audit.domain-events`) und fachlicher `eventType` im Payload.
- Sobald OpenAPI oder AsyncAPI existieren, sollte dieses Kapitel nicht davon abweichen, sondern die lesbare Kurzfassung derselben Contracts sein.

## Weiterfuehrende Detailkapitel

- [Systemarchitektur und Kommunikation](02_systemarchitektur_kommunikation.md)
- [Shop-Service](03_service_shop.md)
- [Warehouse-Service](04_service_warehouse.md)
- [Billing und Invoice](05_service_billing_invoice.md)
- [Audit-Service](06_audit_service.md)
- [Tests, Abnahme und Demo](12_tests_abnahme_demo.md)