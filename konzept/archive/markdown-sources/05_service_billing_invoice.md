# Billing-Service und Invoice-Service

## Billing-Service: Rolle im Gesamtsystem

Der Billing-Service kapselt den Zahlungsfluss. Er kennt die Shop-Bestellung nur über technische und zahlungsrelevante Daten, nicht über Warenkorbdetails. Alle konkreten Zahlungsanbieter werden hinter einer Payment-Fassade verborgen.

## Billing-Verantwortlichkeiten

- Zahlungsversuche anlegen und persistieren.
- Konfigurierten Payment-Anbieter auswählen.
- `charge`, `refund` und `getStatus` über eine einheitliche Schnittstelle ausführen.
- Synchrone und asynchrone Zahlungen unterstützen.
- Webhooks von simulierten Anbietern entgegennehmen.
- Payment-Ergebnisse an den Shop-Service zurückgeben oder zur Fortsetzung bereitstellen.
- `PaymentSucceeded`, `PaymentFailed` und `PaymentRefunded` publizieren.
- Realistische Simulation mit MSW und Faker ermöglichen.

## Billing-API

| Methode | Pfad | Aufrufer | Beschreibung |
| --- | --- | --- | --- |
| `POST` | `/v1/billing/charges` | Shop-Service | Startet Zahlung für eine Bestellung. |
| `POST` | `/v1/billing/refunds` | Shop-Service | Führt Refund für bereits erfolgreiche Zahlung aus. |
| `GET` | `/v1/billing/charges/{correlationId}` | Shop-Service, Admin | Liefert Zahlungsstatus. |
| `POST` | `/v1/billing/webhooks/{provider}` | Payment-Stub | Empfängt asynchrone Bestätigung. |
| `POST` | `/v1/billing/simulation/provider-mode` | `ADMIN` | Setzt Verhalten des Payment-Stubs. |

## Payment-Fassade

Die Fassade ist das wichtigste Erweiterungselement des Billing-Service.

```ts
export interface PaymentProvider {
  charge(request: ChargeRequest): Promise<ChargeResult>;
  refund(request: RefundRequest): Promise<RefundResult>;
  getStatus(providerTransactionId: string): Promise<PaymentStatusResult>;
}
```

Pflichtprinzipien:

- Business-Code ruft niemals direkt `StripeStub`, `KlarnaStub` oder andere Anbieter auf.
- Anbieter werden über eine Factory oder Dependency Injection anhand einer Umgebungsvariable ausgewählt.
- Ein neuer Anbieter implementiert nur das Interface und wird registriert.
- Anbieter-spezifische Fehler werden in kanonische Billing-Fehler übersetzt.

## Provider-Auswahl

Beispielhafte Umgebungsvariablen:

```env
PAYMENT_PROVIDER=stripe-sim
PAYMENT_MODE=sync-success
PAYMENT_WEBHOOK_DELAY_MS=2500
PAYMENT_FORCE_NEXT_RESULT=none
BILLING_PUBLIC_WEBHOOK_BASE_URL=http://billing-service:3000
```

Mögliche Provider:

| Provider | Zweck |
| --- | --- |
| `stripe-sim` | Kartenzahlungsähnliche Simulation. |
| `klarna-sim` | Rechnungskaufähnliche Simulation. |
| `async-webhook-sim` | Gibt `PENDING` zurück und bestätigt später per Webhook. |

## Charge-Ablauf

Request von Shop an Billing:

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

Response bei synchronem Erfolg:

```json
{
  "correlationId": "ord-2026-0001",
  "paymentId": "pay-123",
  "provider": "stripe-sim",
  "providerTransactionId": "txn_abc",
  "status": "SUCCEEDED"
}
```

Response bei asynchronem Anbieter:

```json
{
  "correlationId": "ord-2026-0001",
  "paymentId": "pay-123",
  "provider": "async-webhook-sim",
  "providerTransactionId": "txn_async_abc",
  "status": "PENDING"
}
```

## Zahlungsstatusmodell

| Status | Bedeutung | Endzustand |
| --- | --- | --- |
| `INITIATED` | Payment-Datensatz angelegt. | Nein |
| `PROVIDER_REQUESTED` | Provider wurde aufgerufen. | Nein |
| `PENDING` | Asynchrone Bestätigung ausstehend. | Nein |
| `SUCCEEDED` | Zahlung erfolgreich. | Ja |
| `FAILED` | Zahlung abgelehnt oder technisch endgültig fehlgeschlagen. | Ja |
| `REFUND_REQUESTED` | Refund wurde gestartet. | Nein |
| `REFUNDED` | Zahlung wurde erfolgreich rückerstattet. | Ja |
| `REFUND_FAILED` | Refund fehlgeschlagen, manuelle Prüfung nötig. | Ja |

## Billing-Datenmodell

### `payments`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Payment-ID. |
| `correlation_id` | Text, unique | Bestellprozess. |
| `provider` | Text | Aktiver Provider. |
| `provider_transaction_id` | Text nullable | Externe oder simulierte Transaktions-ID. |
| `amount_gross` | Numeric | Betrag. |
| `currency` | Char(3) | Währung. |
| `status` | Text | Payment-Status. |
| `failure_code` | Text nullable | Kanonischer Fehlercode. |
| `created_at` | Timestamp | Anlage. |
| `updated_at` | Timestamp | Letzte Änderung. |

### `payment_attempts`

Jeder Provider-Aufruf wird separat protokolliert. Dadurch bleiben Retries nachvollziehbar.

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Attempt-ID. |
| `payment_id` | UUID | Payment-Referenz. |
| `operation` | Text | `CHARGE`, `REFUND`, `STATUS`. |
| `request_payload` | JSONB | Maskierter Request. |
| `response_payload` | JSONB | Maskierte Response. |
| `status` | Text | `SUCCESS`, `FAILED`, `TIMEOUT`. |
| `duration_ms` | Integer | Laufzeit. |
| `created_at` | Timestamp | Zeitpunkt. |

## Refund-Ablauf

Ein Refund wird ausgelöst, wenn die Zahlung erfolgreich war, aber die finale Lagerausbuchung scheitert.

Regeln:

- Refunds sind idempotent je `correlationId`.
- Der Billing-Service prüft, ob eine Zahlung mit Status `SUCCEEDED` existiert.
- Provider-spezifische Refund-IDs werden gespeichert.
- Nach erfolgreichem Refund wird `PaymentRefunded` publiziert.
- Bei fehlgeschlagenem Refund muss der Shop-Service `FAILED_REQUIRES_MANUAL_REVIEW` setzen können.

## Asynchroner Webhook-Anbieter

Der asynchrone Stub simuliert realistische Zahlungsflüsse:

1. Shop-Service ruft `POST /v1/billing/charges` auf.
2. Billing-Service legt Payment mit `PENDING` an.
3. Provider-Stub plant einen Webhook nach `PAYMENT_WEBHOOK_DELAY_MS`.
4. Billing-Service antwortet dem Shop-Service mit `PENDING`.
5. Shop-Service setzt Order auf `PAYMENT_PENDING`.
6. Stub sendet `POST /v1/billing/webhooks/{provider}`.
7. Billing-Service validiert die simulierte Signatur.
8. Payment wechselt auf `SUCCEEDED` oder `FAILED`.
9. Billing publiziert ein Event, über das der Shop-Service die Saga fortsetzt oder eine Kompensation startet.

## MSW und Faker

MSW simuliert Provider-HTTP-Endpunkte auf Netzwerkebene. Dadurch bleibt der Adapter-Code realistisch, obwohl keine echten externen Dienste kontaktiert werden.

Faker erzeugt:

- Transaktions-IDs.
- Autorisierungscodes.
- Provider-Fehlermeldungen.
- Webhook-Event-IDs.
- Maskierte Zahlungsdaten für Logs.

Wichtig: Logs dürfen keine echten oder simulierten Vollkartendaten enthalten. Auch Demo-Daten sollten wie sensible Daten behandelt und maskiert werden.

## Billing-Audit-Events

| Event | Bedeutung |
| --- | --- |
| `PaymentInitiated` | Payment-Datensatz angelegt. |
| `PaymentProviderRequested` | Provider-Aufruf gestartet. |
| `PaymentPending` | Provider liefert Pending. |
| `PaymentSucceeded` | Zahlung erfolgreich. |
| `PaymentFailed` | Zahlung abgelehnt oder endgültig fehlgeschlagen. |
| `PaymentRefundRequested` | Refund gestartet. |
| `PaymentRefunded` | Refund erfolgreich. |
| `PaymentRefundFailed` | Refund fehlgeschlagen. |
| `PaymentWebhookReceived` | Webhook eingegangen. |

## Invoice-Service: Rolle im Gesamtsystem

Der Invoice-Service erzeugt PDF-Rechnungen nach erfolgreicher Zahlung. Er wird asynchron über RabbitMQ angestoßen und besitzt keine öffentlichen REST-Endpunkte. Ein Ausfall des Invoice-Service darf nicht automatisch zum Rollback einer erfolgreichen Zahlung führen.

## Invoice-Verantwortlichkeiten

- `PaymentSucceeded`-Events konsumieren.
- Rechnungsdaten validieren.
- PDF-Datei erzeugen.
- Datei in ein Volume schreiben.
- Rechnungsstatus intern protokollieren.
- Circuit-Breaker- und Retry-Zustände auditieren.

## Invoice-Daten und Speicher

Empfohlene Struktur im Volume:

```text
/invoices/
  2026/
    05/
      ord-2026-0001.pdf
```

Optionales Metadatenmodell:

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Rechnungs-ID. |
| `correlation_id` | Text, unique | Bestellung. |
| `invoice_number` | Text | Fachliche Rechnungsnummer. |
| `file_path` | Text | Speicherort. |
| `status` | Text | `GENERATED`, `FAILED`, `RETRY_PENDING`. |
| `created_at` | Timestamp | Erstellung. |

## Invoice-Event-Verarbeitung

1. Event aus RabbitMQ lesen.
2. `correlationId` auf bereits erzeugte Rechnung prüfen.
3. Rechnungspayload validieren.
4. PDF generieren.
5. Datei atomar schreiben.
6. `InvoiceGenerated` auditieren.
7. Message acknlowedgen.

Bei Fehlern:

- Retry bis zur definierten Maximalanzahl.
- Danach Dead-Letter-Queue oder Status `FAILED`.
- Circuit-Breaker-Zustände auditieren.

## Invoice-Audit-Events

| Event | Bedeutung |
| --- | --- |
| `InvoiceGenerationRequested` | Payment-Erfolg löst Rechnung aus. |
| `InvoiceGenerated` | PDF erfolgreich erzeugt. |
| `InvoiceGenerationFailed` | Fehler bei PDF-Erstellung. |
| `InvoiceRetryScheduled` | Retry wird geplant. |
| `CircuitBreakerStateChanged` | Breaker wechselt Zustand. |

## Gemeinsame Risiken

| Risiko | Gegenmaßnahme |
| --- | --- |
| Webhook doppelt empfangen | Webhook-Event-ID und `correlationId` idempotent verarbeiten. |
| Payment erfolgreich, Shop nicht erreichbar | Status im Billing persistieren und Fortsetzung retrybar machen. |
| Refund schlägt fehl | Manuelle Prüfung sichtbar machen, Audit vollständig halten. |
| Invoice-Generierung blockiert Bestellabschluss | Invoice strikt asynchron und nicht als Zahlungskompensation behandeln. |
| Provider-Fehler uneinheitlich | Fehler in kanonische Codes übersetzen. |