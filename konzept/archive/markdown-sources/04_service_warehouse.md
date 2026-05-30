# Warehouse-Service

## Rolle im Gesamtsystem

Der Warehouse-Service ist Eigentümer aller Lagerbestandsdaten. Er entscheidet, ob Ware verfügbar ist, reserviert Bestand temporär und bucht Ware nach erfolgreicher Zahlung endgültig aus. Seine wichtigste technische Aufgabe ist der Schutz vor Überverkäufen bei parallelen Bestellungen.

## Verantwortlichkeiten

- Produktbestände aus Warehouse-Sicht initialisieren.
- Freien und reservierten Bestand verwalten.
- Reservierungen atomar anlegen.
- Reservierungen bei Zahlungsausfall stornieren.
- Reservierte Ware nach erfolgreicher Zahlung final ausbuchen.
- Wareneingänge durch `LOGISTICS` verarbeiten.
- Nebenläufigkeit per PostgreSQL-Sperren kontrollieren.
- Gezielte Fehler für Simulationen auslösen.
- Audit-Events zu Reservierung, Storno und Buchung publizieren.

## Öffentliche interne API

Der Warehouse-Service wird nicht direkt vom Customer Frontend aufgerufen. Zugriffe laufen über den Shop-Service oder kontrollierte interne Admin-Flows.

| Methode | Pfad | Rolle/Aufrufer | Beschreibung |
| --- | --- | --- | --- |
| `POST` | `/v1/warehouse/products` | Shop-Service | Initialisiert Bestand für ein neues Produkt. |
| `PATCH` | `/v1/warehouse/products/{productId}/stock` | `LOGISTICS` | Bucht Wareneingang oder korrigiert Bestand. |
| `GET` | `/v1/warehouse/products/{productId}/stock` | `LOGISTICS`, `ADMIN` | Liefert freien, reservierten und gebuchten Bestand. |
| `POST` | `/v1/warehouse/reservations` | Shop-Service | Prüft und reserviert Bestand. |
| `DELETE` | `/v1/warehouse/reservations/{correlationId}` | Shop-Service | Storniert Reservierung. |
| `POST` | `/v1/warehouse/bookings` | Shop-Service | Bucht reservierte Ware endgültig aus. |
| `POST` | `/v1/warehouse/simulation/failure-mode` | `ADMIN` | Aktiviert einen einmaligen oder dauerhaften Fehlerzustand. |

## Datenmodell

### `warehouse_products`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `product_id` | UUID | Produkt-ID aus dem Shop-Service. |
| `sku` | Text | Artikelnummer. |
| `available_quantity` | Integer | Frei verfügbarer Bestand. |
| `reserved_quantity` | Integer | Temporär reservierter Bestand. |
| `booked_quantity` | Integer | Historisch final ausgebuchte Menge. |
| `version` | Integer | Optional für zusätzliche Optimistic-Lock-Diagnose. |
| `created_at` | Timestamp | Anlage. |
| `updated_at` | Timestamp | Letzte Änderung. |

### `reservations`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `id` | UUID | Reservierungs-ID. |
| `correlation_id` | Text, unique | Prozess-ID der Bestellung. |
| `status` | Text | `ACTIVE`, `CANCELLED`, `BOOKED`, `EXPIRED`. |
| `created_at` | Timestamp | Anlagezeit. |
| `expires_at` | Timestamp nullable | Optionales Ablaufdatum. |

### `reservation_items`

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `reservation_id` | UUID | Referenz auf Reservierung. |
| `product_id` | UUID | Produkt. |
| `quantity` | Integer | Reservierte Menge. |

### `stock_movements`

Diese Tabelle dokumentiert Bewegungen aus Warehouse-Sicht:

| Feld | Typ | Beispiel |
| --- | --- | --- |
| `id` | UUID | Bewegungs-ID. |
| `product_id` | UUID | Betroffener Artikel. |
| `movement_type` | Text | `INBOUND`, `RESERVED`, `RESERVATION_CANCELLED`, `BOOKED`. |
| `quantity_delta` | Integer | `+10`, `-2`. |
| `correlation_id` | Text nullable | Bezug zur Bestellung. |
| `created_by` | Text | Service oder Nutzer. |
| `created_at` | Timestamp | Zeitpunkt. |

## Reservierungsablauf

Request:

```json
{
  "correlationId": "ord-2026-0001",
  "items": [
    { "productId": "prd-1", "quantity": 1 },
    { "productId": "prd-2", "quantity": 2 }
  ]
}
```

Ablauf:

1. `correlationId` auf bestehende aktive Reservierung prüfen.
2. Datenbanktransaktion starten.
3. Alle betroffenen Produktzeilen in stabiler Reihenfolge sperren.
4. Verfügbarkeit prüfen.
5. Falls Bestand reicht: `available_quantity` reduzieren und `reserved_quantity` erhöhen.
6. Reservierung und Positionen anlegen.
7. Stock Movements schreiben.
8. Transaktion committen.
9. `ReservationCreated` publizieren.

## Pessimistic Locking

Der kritische Abschnitt liegt vollständig in einer PostgreSQL-Transaktion. Die Produktzeilen werden mit `SELECT ... FOR UPDATE` gesperrt.

Beispielhafte SQL-Strategie:

```sql
BEGIN;

SELECT product_id, available_quantity, reserved_quantity
FROM warehouse_products
WHERE product_id = ANY($1)
ORDER BY product_id
FOR UPDATE;

-- Verfügbarkeit in der Applikationslogik prüfen.
-- Danach atomare Updates je Produkt ausführen.

UPDATE warehouse_products
SET available_quantity = available_quantity - $quantity,
    reserved_quantity = reserved_quantity + $quantity,
    updated_at = NOW()
WHERE product_id = $productId;

COMMIT;
```

Das `ORDER BY product_id` ist wichtig, wenn mehrere Produkte in einer Reservierung vorkommen. Es reduziert Deadlock-Risiken, weil konkurrierende Transaktionen Sperren in derselben Reihenfolge anfordern.

## Storno einer Reservierung

`DELETE /v1/warehouse/reservations/{correlationId}` wird bei Zahlungsfehlern aufgerufen.

Regeln:

- Nur `ACTIVE`-Reservierungen können storniert werden.
- Die zugehörigen Produktzeilen werden ebenfalls per `FOR UPDATE` gesperrt.
- `reserved_quantity` wird reduziert.
- `available_quantity` wird erhöht.
- Reservierung erhält Status `CANCELLED`.
- Operation ist idempotent: ein zweiter Storno liefert denselben fachlichen Erfolg, verändert aber keine Mengen erneut.

## Finale Buchung

`POST /v1/warehouse/bookings` bucht reservierte Ware endgültig aus.

Regeln:

- Nur `ACTIVE`-Reservierungen können gebucht werden.
- Die Buchung reduziert `reserved_quantity`.
- `booked_quantity` wird erhöht.
- Die Reservierung erhält Status `BOOKED`.
- Bei aktivierter Fehlersimulation kann der Endpunkt vor dem Commit fehlschlagen.
- Die Operation ist idempotent für dieselbe `correlationId`.

## Wareneingang und Korrektur

Logistik-Mitarbeiter verwenden:

```http
PATCH /v1/warehouse/products/{productId}/stock
```

Request:

```json
{
  "quantityDelta": 15,
  "reason": "INBOUND_DELIVERY",
  "reference": "DEL-2026-05-29-001"
}
```

Regeln:

- Positive Deltas erhöhen den freien Bestand.
- Negative Deltas sind nur für Korrekturen erlaubt und dürfen den freien Bestand nicht unter `0` senken.
- Jede Änderung erzeugt ein `StockAdjusted`-Audit-Event.
- Der ausführende Nutzer wird im Movement gespeichert.

## Fehler- und Simulation-Modi

| Modus | Wirkung | Demo-Zweck |
| --- | --- | --- |
| `FAIL_NEXT_BOOKING` | Nächste finale Buchung schlägt fehl. | Refund-Kompensation demonstrieren. |
| `DELAY_RESERVATION` | Reservierung wird künstlich verzögert. | Idempotenz und UI-Loading testen. |
| `FORCE_OUT_OF_STOCK` | Reservierung wird abgelehnt. | Out-of-stock-Pfad demonstrieren. |
| `LOCK_HOLD_MS` | Transaktion hält Sperre bewusst länger. | Concurrency sichtbar machen. |

Simulation-Modi müssen begrenzt sein. Ein einmaliger Fehler ist für Präsentationen sicherer als ein global dauerhaft kaputter Service.

## Concurrency-Test

Der wichtigste Nebenläufigkeitstest:

1. Produktbestand auf `1` setzen.
2. Zwei parallele Bestellungen für dasselbe Produkt starten.
3. Beide Requests erreichen `POST /v1/warehouse/reservations` nahezu gleichzeitig.
4. Die erste Transaktion sperrt die Zeile und reserviert den Bestand.
5. Die zweite Transaktion wartet, liest nach Commit den neuen Bestand `0` und lehnt sauber ab.
6. Ergebnis: genau eine Bestellung kann fortfahren, die andere endet mit `OUT_OF_STOCK`.

## Audit-Events

| Event | Inhalt |
| --- | --- |
| `WarehouseProductInitialized` | `productId`, `sku`, initialer Bestand. |
| `StockAdjusted` | Delta, Grund, Nutzer, neuer Bestand. |
| `ReservationCreated` | Positionen, Mengen, vorher/nachher Werte. |
| `ReservationRejected` | Produkt, angefragte Menge, verfügbarer Bestand. |
| `ReservationCancelled` | Freigegebene Mengen. |
| `StockBooked` | Final gebuchte Mengen. |
| `WarehouseFailureInjected` | Aktiver Simulationsmodus. |

## Invarianten

- `available_quantity >= 0`.
- `reserved_quantity >= 0`.
- `booked_quantity >= 0`.
- Eine `correlationId` hat maximal eine aktive Reservierung.
- Eine Reservierung kann nicht gleichzeitig `CANCELLED` und `BOOKED` sein.
- Finale Buchung darf Bestand nicht aus `available_quantity` abbuchen, sondern nur aus `reserved_quantity`.

## Implementierungshinweise

- Kritische Operationen laufen in einer Datenbanktransaktion.
- Deadlocks werden geloggt und mit begrenztem Retry behandelt.
- Sperren werden möglichst kurz gehalten.
- Fehler nach Commit dürfen keine doppelten Mengenänderungen auslösen.
- Alle Mengenoperationen sind integerbasiert, keine Gleitkommazahlen.
- Idempotente Endpunkte prüfen zuerst vorhandene Reservierung oder Buchung zur `correlationId`.