# Shop-Service

## Rolle im Gesamtsystem

Der Shop-Service ist der zentrale Eintrittspunkt des Systems. Er übernimmt die Funktion eines API-Gateways, hält die kundenbezogenen Shop-Daten und orchestriert den verteilten Bestellprozess. Kein Frontend spricht direkt mit Warehouse, Billing, Invoice oder Audit. Dadurch bleibt die externe API konsistent und die interne Topologie kann verändert werden, ohne die Clients anzupassen.

## Verantwortlichkeiten

Der Shop-Service verantwortet:

- Registrierung und Login.
- JWT-Ausstellung und Rolleninformationen.
- Produktkatalog aus Shop-Sicht.
- Warenkorbverwaltung pro Nutzer.
- Bestellerstellung aus dem Warenkorb.
- Idempotenz für `POST /v1/orders`.
- Saga-Orchestrierung über Warehouse und Billing.
- Statusmodell der Bestellung.
- Weitergabe von `correlationId` und `X-Idempotency-Key`.
- Veröffentlichung von Audit-relevanten Domain-Events.

## Interne Module

| Modul | Aufgabe |
| --- | --- |
| `AuthModule` | Registrierung, Login, Passwort-Hashing, JWT-Ausstellung. |
| `UsersModule` | Nutzerprofile, Rollen, interne User-Abfragen. |
| `ProductsModule` | Produktkatalog, Produktanlage, Produktstatus. |
| `BasketModule` | Aktiver Warenkorb, Positionen, Mengenänderungen. |
| `OrdersModule` | Bestellungen, Statuswechsel, Abfragen. |
| `SagaModule` | Orchestrierter Bestellablauf und Kompensationslogik. |
| `IdempotencyModule` | Redis-basierte Erkennung wiederholter Requests. |
| `ClientsModule` | Typed HTTP-Clients für Warehouse und Billing. |
| `AuditPublisherModule` | Publikation von Domain-Events in Richtung Audit. |

## Öffentliche API

### Authentifizierung

| Methode | Pfad | Rolle | Beschreibung |
| --- | --- | --- | --- |
| `POST` | `/v1/auth/register` | Öffentlich | Erstellt einen neuen Nutzer mit Standardrolle `CUSTOMER`. |
| `POST` | `/v1/auth/login` | Öffentlich | Prüft Credentials und gibt Access Token aus. |

Register-Request:

```json
{
  "email": "kunde@example.local",
  "password": "change-me",
  "displayName": "Max Muster"
}
```

Login-Response:

```json
{
  "accessToken": "jwt-token",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": {
    "id": "usr_...",
    "email": "kunde@example.local",
    "roles": ["CUSTOMER"]
  }
}
```

### Produktmanagement

| Methode | Pfad | Rolle | Beschreibung |
| --- | --- | --- | --- |
| `GET` | `/v1/products` | Öffentlich | Paginierte und filterbare Produktliste. |
| `GET` | `/v1/products/{productId}` | Öffentlich | Detailansicht eines Produkts. |
| `POST` | `/v1/products` | `ADMIN` | Erstellt ein Produkt und initialisiert den Warehouse-Datensatz. |
| `PATCH` | `/v1/products/{productId}` | `ADMIN` | Bearbeitet Produktdaten aus Shop-Sicht. |

Produktanlage:

```json
{
  "name": "USB-C Docking Station",
  "description": "Docking Station mit HDMI, Ethernet und Power Delivery.",
  "priceGross": 129.99,
  "currency": "EUR",
  "sku": "DOCK-USB-C-001",
  "initialStock": 25,
  "active": true
}
```

Nach erfolgreicher Produktanlage ruft der Shop-Service synchron den Warehouse-Service auf, um den Bestandssatz mit `productId`, `sku` und `initialStock` anzulegen. Schlägt diese Initialisierung fehl, wird die Produktanlage zurückgerollt oder als `PENDING_STOCK_INITIALIZATION` markiert. Für ein Uni-Projekt ist ein Rollback der lokalen Produktanlage am klarsten demonstrierbar.

### Warenkorb

| Methode | Pfad | Rolle | Beschreibung |
| --- | --- | --- | --- |
| `GET` | `/v1/baskets` | `CUSTOMER` | Gibt den aktiven Warenkorb zurück. |
| `POST` | `/v1/baskets/items` | `CUSTOMER` | Fügt ein Produkt hinzu oder erhöht die Menge. |
| `PATCH` | `/v1/baskets/items/{productId}` | `CUSTOMER` | Setzt die Menge einer Position. |
| `DELETE` | `/v1/baskets/items/{productId}` | `CUSTOMER` | Entfernt eine Position vollständig. |

Warenkorbpositionen speichern Preis-Snapshots. Damit bleibt nachvollziehbar, zu welchem Preis der Nutzer bestellt hat, auch wenn sich der Produktpreis später ändert.

### Bestellung

| Methode | Pfad | Rolle | Beschreibung |
| --- | --- | --- | --- |
| `POST` | `/v1/orders` | `CUSTOMER` | Wandelt den Warenkorb in eine Bestellung und startet die Saga. |
| `GET` | `/v1/orders/{correlationId}` | `CUSTOMER`, `ADMIN` | Gibt aktuellen Status und grobe Prozessinformationen zurück. |
| `GET` | `/v1/orders` | `CUSTOMER`, `ADMIN` | Listet eigene oder alle Bestellungen abhängig von Rolle. |

Pflichtheader für `POST /v1/orders`:

```http
Authorization: Bearer <jwt>
X-Idempotency-Key: <client-generated-key>
X-Correlation-Id: <optional-client-correlation-id>
```

Wenn kein `X-Correlation-Id` vorhanden ist, erzeugt der Shop-Service eine neue ID und gibt sie in der Antwort zurück.

## Datenmodell

### `users`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Primärschlüssel. |
| `email` | Text, unique | Login-Identifier. |
| `password_hash` | Text | Hash, niemals Klartext. |
| `display_name` | Text | Anzeigename. |
| `roles` | Text[] oder Join-Tabelle | Rollen wie `CUSTOMER`, `ADMIN`, `LOGISTICS`. |
| `created_at` | Timestamp | Anlagezeitpunkt. |
| `updated_at` | Timestamp | Letzte Änderung. |

### `products`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Shop-weite Produkt-ID, wird auch an Warehouse gereicht. |
| `sku` | Text, unique | Fachliche Artikelnummer. |
| `name` | Text | Produktname. |
| `description` | Text | Beschreibung. |
| `price_gross` | Numeric | Bruttopreis. |
| `currency` | Char(3) | ISO-Währung, z. B. `EUR`. |
| `active` | Boolean | Sichtbarkeit im Katalog. |

### `baskets` und `basket_items`

Der Warenkorb ist persistent. Dadurch kann die Customer View nach Reload oder Login den Zustand wiederherstellen.

Wichtige Regeln:

- Pro Nutzer gibt es maximal einen aktiven Warenkorb.
- Mengen müssen positiv sein.
- Inaktive Produkte dürfen nicht neu hinzugefügt werden.
- Beim Checkout werden Produktdaten als Order-Snapshot kopiert.

### `orders` und `order_items`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Interne Order-ID. |
| `correlation_id` | UUID/Text | Prozessweite ID. |
| `user_id` | UUID | Bestellender Nutzer. |
| `status` | Text | Status aus dem Order-Statusmodell. |
| `total_gross` | Numeric | Gesamtbetrag. |
| `currency` | Char(3) | Währung. |
| `idempotency_key` | Text | Verknüpfung zum Request-Key. |
| `created_at` | Timestamp | Anlage. |
| `completed_at` | Timestamp nullable | Abschlusszeitpunkt. |

## Bestellstatusmodell

| Status | Bedeutung | Endzustand |
| --- | --- | --- |
| `CREATED` | Bestellung lokal angelegt. | Nein |
| `RESERVATION_PENDING` | Warehouse-Reservierung wird ausgeführt. | Nein |
| `RESERVED` | Bestand ist temporär reserviert. | Nein |
| `PAYMENT_PENDING` | Zahlung wartet, z. B. auf Webhook. | Nein |
| `PAYMENT_FAILED` | Zahlung abgelehnt, Reservierung kompensiert. | Ja |
| `OUT_OF_STOCK` | Lagerbestand reicht nicht. | Ja |
| `BOOKING_PENDING` | Finale Ausbuchung läuft. | Nein |
| `ROLLBACK_PENDING` | Kompensation läuft. | Nein |
| `ROLLBACK_COMPLETED` | Kompensation nach Fehler abgeschlossen. | Ja |
| `COMPLETED` | Zahlung, Ausbuchung und Abschluss erfolgreich. | Ja |
| `FAILED_REQUIRES_MANUAL_REVIEW` | Unerwarteter Fehler nach Teilabschluss. | Ja, operativ zu prüfen |

## Saga-Orchestrierung

Der Shop-Service führt die Saga explizit als Zustandsmaschine aus. Jeder Schritt schreibt zunächst den lokalen Status, publiziert einen Audit-Snapshot und ruft dann den nächsten Service auf.

Empfohlene Orchestrator-Schritte:

1. Request validieren und Idempotenz prüfen.
2. Warenkorb laden und Positionen einfrieren.
3. Order mit `CREATED` anlegen.
4. Status `RESERVATION_PENDING` setzen.
5. Warehouse-Reservierung aufrufen.
6. Bei Erfolg Status `RESERVED` setzen.
7. Billing-Charge aufrufen.
8. Bei synchronem Erfolg finale Warehouse-Buchung auslösen.
9. Bei `PENDING` Status `PAYMENT_PENDING` setzen und auf Webhook-Fortsetzung warten.
10. Bei Payment-Fehler Reservierung stornieren und `PAYMENT_FAILED` setzen.
11. Bei Booking-Erfolg `COMPLETED` setzen und Warenkorb leeren.
12. Bei Booking-Fehler Refund auslösen und `ROLLBACK_COMPLETED` setzen.

## Idempotenzintegration

Der Shop-Service prüft bei `POST /v1/orders` den `X-Idempotency-Key` vor Beginn der Saga. Die Verarbeitung sollte drei Zustände kennen:

| Zustand | Verhalten |
| --- | --- |
| Key unbekannt | Lock in Redis setzen und Verarbeitung starten. |
| Key in Bearbeitung | `409` oder `202` mit Link auf Status zurückgeben. |
| Key abgeschlossen | Ursprüngliche Antwort aus Redis oder Datenbank erneut liefern. |

Die Kombination aus `userId` und `idempotencyKey` muss eindeutig sein, damit zwei verschiedene Nutzer denselben zufälligen Key verwenden können, ohne sich zu blockieren.

## Audit-Events des Shop-Service

| Event | Auslöser |
| --- | --- |
| `OrderCreated` | Order lokal angelegt. |
| `OrderReservationRequested` | Warehouse-Reservierung wird gestartet. |
| `OrderPaymentRequested` | Billing-Charge wird gestartet. |
| `OrderPaymentPending` | Payment-Fassade liefert Pending. |
| `OrderBookingRequested` | Finale Lagerbuchung wird gestartet. |
| `OrderCompleted` | Saga erfolgreich abgeschlossen. |
| `OrderFailedOutOfStock` | Warehouse lehnt Reservierung ab. |
| `OrderFailedPayment` | Billing lehnt Zahlung ab. |
| `OrderRollbackStarted` | Kompensation nach Teilfehler beginnt. |
| `OrderRollbackCompleted` | Refund oder Reservierungsstorno abgeschlossen. |

## Validierungsregeln

- Warenkorb darf nicht leer sein.
- Produkt muss aktiv sein.
- Menge muss größer als `0` sein.
- Währung aller Positionen muss identisch sein.
- Nutzer muss Rolle `CUSTOMER` besitzen.
- `X-Idempotency-Key` ist für Bestellungen verpflichtend.
- Preis-Snapshot wird beim Checkout fixiert.
- Der Warenkorb wird erst nach erfolgreichem Saga-Abschluss geleert.

## Fehlerfälle

| Fehler | Reaktion |
| --- | --- |
| Warenkorb leer | `400` Problem Details, keine Saga. |
| Lager nicht ausreichend | Order `OUT_OF_STOCK`, keine Payment-Anfrage. |
| Payment abgelehnt | Reservierung stornieren, Order `PAYMENT_FAILED`. |
| Billing nicht erreichbar | Retry nach Policy, danach Kompensation und technischer Fehlerstatus. |
| Warehouse-Booking schlägt fehl | Refund auslösen, Order `ROLLBACK_COMPLETED`. |
| Audit-Service nicht erreichbar | Business-Prozess nicht blockieren, Event retrybar puffern. |

## Implementierungshinweise für NestJS

- Controller bleiben dünn und delegieren an Application Services.
- Externe HTTP-Clients werden über Adapter gekapselt.
- Rollenprüfung erfolgt über Guards und Decorators.
- Transaktionen für lokale Order-Anlage laufen über Repository/ORM-Transaktionsmechanismen.
- Saga-Schritte sollten explizit typisiert sein, nicht als lose String-Ketten.
- Statuswechsel werden zentral validiert, damit unmögliche Übergänge auffallen.