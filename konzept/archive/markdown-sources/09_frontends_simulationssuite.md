# Frontends und Simulationssuite

## Ziel der Frontend-Architektur

Die Frontends sollen nicht nur Bedienoberflächen sein, sondern die verteilte Architektur sichtbar machen. Besonders für Präsentation und Bewertung ist entscheidend, dass Bestellstatus, Audit-Snapshots, Lagerbewegungen, Payment-Zustände und Fehlerpfade nachvollziehbar dargestellt werden.

## Frontend-Landkarte

| Frontend | Zielgruppe | Hauptzweck |
| --- | --- | --- |
| Customer Storefront | Kunden | Einkauf, Warenkorb, Checkout, Bestellstatus. |
| Admin Dashboard | Admins, Prüfer | Bestellungen, Audit-Timeline, technische Analyse. |
| Warehouse WMS | Logistik | Bestandsmonitor, Wareneingänge, Reservierungen. |
| Simulation Panel | Präsentierende, Entwickler | Happy Path, Fehler, Concurrency und Webhook-Latenz steuern. |

## Gemeinsame Frontend-Grundsätze

- Alle Business-APIs laufen über den Shop-Service.
- JWT wird zentral verwaltet.
- `X-Correlation-Id` wird angezeigt, sobald sie vorhanden ist.
- Lange Saga-Schritte werden als Prozesszustände visualisiert.
- Fehler werden mit Problem-Details-Code und verständlicher Kurzmeldung angezeigt.
- Admin-Views bieten technische Details, Customer-Views bleiben nutzerfreundlich.

## Customer Storefront

### Zweck

Die Storefront simuliert das Einkaufserlebnis. Sie muss einfach genug für eine Demo sein, aber realistisch genug, um Warenkorb, Checkout und asynchrone Zustände sichtbar zu machen.

### Hauptseiten

| Route | Inhalt |
| --- | --- |
| `/login` | Login und Registrierung. |
| `/products` | Produktliste mit Filterung und Paginierung. |
| `/products/:id` | Produktdetails. |
| `/basket` | Warenkorb mit Mengensteuerung. |
| `/checkout` | Bestellauslösung und Zahlungsdaten-Simulation. |
| `/orders/:correlationId` | Bestellstatus und Fortschritt. |

### Erwartete Komponenten

- Produktkarte mit Preis, Verfügbarkeitshinweis und Warenkorb-Aktion.
- Warenkorbposition mit Menge, Einzelpreis und Summe.
- Checkout-Button mit Idempotenzschutz gegen Doppelklick.
- Prozessanzeige für Saga-Schritte.
- Statushinweise für `PAYMENT_PENDING`, `COMPLETED`, `OUT_OF_STOCK` und `PAYMENT_FAILED`.

### Idempotenz in der UI

Die UI soll bei Klick auf Kaufen:

- Einen neuen `X-Idempotency-Key` erzeugen.
- Den Button während der laufenden Anfrage deaktivieren.
- Bei Netzwerkfehler Wiederholen mit demselben Key erlauben.
- Die erhaltene `correlationId` speichern.
- Den Nutzer auf die Bestellstatus-Seite führen.

## Admin Dashboard

### Zweck

Das Admin Dashboard ist die technische Beobachtungszentrale. Es zeigt alle Bestellungen, ihren Status und die vollständige Audit-Timeline.

### Hauptseiten

| Route | Inhalt |
| --- | --- |
| `/admin/orders` | Tabelle aller Bestellungen. |
| `/admin/orders/:correlationId` | Detailansicht mit Audit-Timeline. |
| `/admin/products/new` | Produktanlage. |
| `/admin/audit` | Audit-Suche und Stream. |
| `/admin/simulation` | Link oder eingebettetes Simulation Panel. |

### Order-Tabelle

Spalten:

- `correlationId`.
- Nutzer oder Customer-ID.
- Status.
- Gesamtbetrag.
- Zeitpunkt.
- Payment-Status.
- Warehouse-Status.
- Anzahl Audit-Events.

Filter:

- Status.
- Zeitraum.
- `correlationId`.
- Fehlercode.
- Service.

### Audit-Timeline

Die Timeline zeigt pro Event:

- Zeitpunkt.
- Quelle.
- Eventtyp.
- Kurzbeschreibung.
- Statuschip.
- Aufklappbarer JSON-Payload.
- Link zu Logs mit derselben `correlationId`.

Die Timeline aktualisiert sich live über SSE oder WebSocket.

## Warehouse WMS

### Zweck

Das WMS macht Lagerzustände sichtbar. Es richtet sich an Logistik-Mitarbeiter und ist gleichzeitig ein Demonstrationswerkzeug für Reservierung und finale Ausbuchung.

### Hauptseiten

| Route | Inhalt |
| --- | --- |
| `/warehouse/stocks` | Bestandstabelle. |
| `/warehouse/products/:productId` | Detail mit Bewegungen. |
| `/warehouse/inbound` | Wareneingang erfassen. |
| `/warehouse/reservations` | Aktive und abgeschlossene Reservierungen. |

### Bestandstabelle

Spalten:

- Produktname und SKU.
- Freier Bestand.
- Reservierter Bestand.
- Gebuchter Bestand.
- Letzte Bewegung.
- Warnstatus bei niedrigem Bestand.

### Wareneingang

Die Wareneingangsmaske sendet `PATCH /v1/warehouse/products/{productId}/stock` über den Shop-Service oder ein internes Gateway.

Pflichtfelder:

- Produkt.
- Menge.
- Grund.
- Referenz.

## Simulation Panel

## Zweck

Das Simulation Panel ist das Live-Demo-Control-Panel. Es erzeugt kontrollierte Systemzustände, ohne dass man während der Präsentation manuell Datenbanken manipulieren muss.

## Funktionen

| Funktion | Wirkung |
| --- | --- |
| Happy-Path-Trigger | Erzeugt Musterwarenkorb und startet Bestellung. |
| Payment-Ablehnung | Nächster Payment-Aufruf schlägt fehl. |
| Warehouse-Booking-Fehler | Nächste finale Ausbuchung schlägt fehl. |
| Invoice-Crash | Invoice-Service wirft Fehler und öffnet Circuit Breaker. |
| Concurrency-Test | Zwei parallele Bestellungen auf denselben knappen Bestand. |
| Webhook-Latenz | Slider steuert Verzögerung des asynchronen Payment-Stubs. |
| Daten zurücksetzen | Demo-Daten werden in definierten Startzustand gebracht. |

## Demo-Workflow im Panel

1. Demo-Datensatz initialisieren.
2. Produktbestand und Nutzer prüfen.
3. Gewünschtes Szenario auswählen.
4. Start klicken.
5. Live-Verlinkung zu Admin-Timeline öffnen.
6. Logs oder Grafana-Panel zur `correlationId` anzeigen.

## Zustandsvisualisierung

Die Simulation View sollte eine technische Prozessleiste anzeigen:

```text
Order Created -> Reserved -> Payment -> Booking -> Completed
```

Bei Fehlern werden Kompensationsschritte sichtbar ergänzt:

```text
Order Created -> Reserved -> Payment Failed -> Reservation Cancelled -> Payment Failed
```

## API-Bedarf der Frontends

Die Frontends benötigen gebündelte View-Endpunkte, damit sie nicht zu viel interne Service-Logik kennen.

Empfohlene Shop-Endpunkte:

| Endpunkt | Zweck |
| --- | --- |
| `GET /v1/me` | Aktueller Nutzer und Rollen. |
| `GET /v1/products` | Produktliste. |
| `GET /v1/baskets` | Warenkorb. |
| `POST /v1/orders` | Checkout starten. |
| `GET /v1/orders/{correlationId}` | Statuspolling oder Detail. |
| `GET /v1/admin/orders` | Admin-Tabelle. |
| `GET /v1/admin/orders/{correlationId}/timeline` | Kombinierte Order- und Audit-Sicht. |
| `GET /v1/admin/audit/stream` | Live-Events. |
| `POST /v1/admin/simulation/*` | Simulationssteuerung. |

## Frontend-Zustandsmanagement

Empfohlen:

- React Query oder vergleichbare Datenbibliothek für Server State.
- Lokaler State nur für UI-Zustände wie Dialoge und Filter.
- SSE-Verbindung im Admin Dashboard für Live-Audit.
- Optimistische Updates nur bei ungefährlichen UI-Aktionen, nicht bei Checkout.

## Rollenabhängige Navigation

| Rolle | Sichtbare Bereiche |
| --- | --- |
| `CUSTOMER` | Storefront, Warenkorb, eigene Bestellungen. |
| `ADMIN` | Admin Dashboard, Produkterstellung, Simulation, Audit. |
| `LOGISTICS` | Warehouse WMS, Wareneingang, Bestand. |

## Demo-Anforderungen

Für die Präsentation sollten alle Views mit wenigen Klicks verständliche Zustände erzeugen:

- Ein Klick für Happy Path.
- Ein Klick für Payment-Fehler.
- Ein Klick für Warehouse-Booking-Fehler.
- Ein Klick für Concurrency-Test.
- Slider für Webhook-Latenz.
- Direkter Link zur Audit-Timeline jeder gestarteten Demo-Bestellung.

## Akzeptanzkriterien

- Customer kann eine Bestellung starten und den Status sehen.
- Admin sieht alle Audit-Snapshots ohne Reload.
- WMS zeigt freie und reservierte Bestände korrekt.
- Simulation Panel kann definierte Fehler reproduzierbar auslösen.
- Die UI zeigt `correlationId` an technischen Stellen sichtbar an.
- Fehlerzustände sind verständlich, aber nicht mit internen Stacktraces vermischt.