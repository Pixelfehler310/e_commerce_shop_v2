# Anforderungsdokument Distributed E-Commerce Core

## 1. Einordnung und Zielsetzung

Der Distributed E-Commerce Core ist ein verteilter fachlicher Kern für einen Online-Shop mit getrennten Backend-Services, mehreren Frontend-Sichten, nachvollziehbarer Bestellabwicklung und gezielt demonstrierbaren Fehlerfällen. Das System bildet Produktauswahl, Warenkorb, Bestellung, Bestandsreservierung, Zahlung, asynchrone Rechnungsstellung, Audit-Timeline und Kompensation in einem konsistenten Gesamtprozess ab.

Das Ziel des Systems besteht darin, einen realitätsnahen Microservice-Verbund bereitzustellen, der fachliche Datenhoheit respektiert, lokale Transaktionen pro Service nutzt, verteilte Konsistenz über eine orchestrierte Saga herstellt und alle relevanten Zustandsänderungen nachvollziehbar in Logs, Metriken und Audit-Snapshots sichtbar macht.

| ID | Anforderung | Akzeptanzkriterium |
| --- | --- | --- |
| SYS-GOAL-001 | Das System muss einen vollständigen E-Commerce-Bestellprozess von Produktauswahl bis Rechnungsbereitstellung abbilden. | Ein Kunde kann eine Bestellung auslösen, die erfolgreich abgeschlossen oder nachvollziehbar fachlich abgelehnt wird. |
| SYS-GOAL-002 | Das System muss Service-Verantwortlichkeiten fachlich trennen und direkte Fremd-Datenbankzugriffe ausschließen. | Jeder Service besitzt eigene Persistenz und alle serviceübergreifenden Zugriffe erfolgen über REST oder Events. |
| SYS-GOAL-003 | Das System muss Fehler-, Pending- und Kompensationspfade als reguläre Systemfunktionen behandeln. | Payment-Fehler, Lagerengpass, Booking-Fehler, Webhook-Pending und Invoice-Ausfall sind reproduzierbar auslösbar und auditierbar. |
| SYS-GOAL-004 | Das System muss für Architekturabgleich, Umsetzung, Testableitung und Abnahme prüfbare Anforderungen bereitstellen. | Jede zentrale Funktion ist einer Anforderungskennung und einem prüfbaren Nachweis zugeordnet. |

## 2. Dokumentzweck und Abgrenzung

Dieses Dokument definiert verbindliche fachliche und technische Anforderungen an den Distributed E-Commerce Core. Es beschreibt Systemgrenzen, Rollen, funktionale Anforderungen, nichtfunktionale Anforderungen, Kommunikationsanforderungen, Daten- und Konsistenzregeln, Betriebsanforderungen, Testanforderungen und Abnahmekriterien.

Das Dokument dient als Grundlage für Implementierung, Architekturentscheidungen, Testfallableitung, Review, Demonstration und fachliche Abnahme. Es ersetzt keine detaillierte API-Spezifikation, keine Datenbankmigrationen und keine konkrete UI-Komponentenspezifikation, legt jedoch die Anforderungen fest, aus denen diese Artefakte abzuleiten sind.

| ID | Bereich | Festlegung |
| --- | --- | --- |
| DOC-SCOPE-001 | Enthalten | Backend-Services, Frontends, Saga, Persistenz, Kommunikation, Security, Observability, Tests, Demo-Fähigkeit. |
| DOC-SCOPE-002 | Enthalten | Anforderungen an Happy Path, Negativpfade, Kompensation, Pending-Zustände, Retry und Concurrency. |
| DOC-SCOPE-003 | Nicht enthalten | Produktives Payment-Onboarding mit echten Zahlungsdaten und regulatorische Zertifizierungen für reale Zahlungsabwicklung. |
| DOC-SCOPE-004 | Nicht enthalten | Vollständige Enterprise-Mandantenfähigkeit, globaler Multi-Region-Betrieb und produktive Hochverfügbarkeitscluster. |

## 3. Stakeholder, Rollen und Berechtigungen

Das System unterscheidet fachliche Benutzerrollen, technische Service-Identitäten und operative Rollen. Alle schreibenden oder sensiblen Aktionen müssen über Authentisierung, Autorisierung und Auditierbarkeit abgesichert werden.

| Rolle | Zweck | Zulässige Kernaktionen | Einschränkungen |
| --- | --- | --- | --- |
| CUSTOMER | Endkunde im Shop | Produkte ansehen, Warenkorb pflegen, Bestellung auslösen, eigene Bestellung einsehen. | Kein Zugriff auf fremde Bestellungen, interne Services, Simulation oder Lagerverwaltung. |
| ADMIN | Fachlicher und technischer Administrator | Bestellungen, Audit-Timelines, Simulation, Systemstatus und Demo-Szenarien einsehen oder steuern. | Keine direkten Datenbankänderungen über die UI. |
| LOGISTICS | Lagerrolle | Bestand prüfen, Wareneingang buchen, Reservierungen und Buchungen einsehen. | Kein Zugriff auf Payment-Konfiguration und Kundengeheimnisse. |
| DEMO_OPERATOR | Präsentationsrolle | Szenarien vorbereiten, Fehlerflags setzen, Demo-Daten zurücksetzen, parallele Tests starten. | Nur in lokaler oder freigegebener Demo-Umgebung aktiv. |
| SERVICE | Technische Service-Identität | Interne REST-Aufrufe, Event-Publishing, Event-Consumption, Healthchecks. | Keine Nutzung über öffentliche Frontend-Kontexte. |

### Rollenanforderungen

| ID | Anforderung | Akzeptanzkriterium |
| --- | --- | --- |
| SEC-RBAC-001 | Jede geschützte Aktion muss einer Rolle oder Service-Identität zugeordnet sein. | Zugriff ohne gültiges Token oder ohne ausreichende Rolle wird mit Problem Details abgelehnt. |
| SEC-RBAC-002 | Admin- und Simulation-Funktionen müssen von Customer-Funktionen getrennt sein. | Ein CUSTOMER kann keine Simulation-Flags setzen und keine Audit-Timelines fremder Bestellungen lesen. |
| SEC-RBAC-003 | LOGISTICS darf Lagerdaten ändern, aber keine Zahlungen refundieren oder Payment-Provider steuern. | WMS-Aktionen sind auf Warehouse-APIs und lagerbezogene Shop-Proxies begrenzt. |
| SEC-RBAC-004 | Technische Service-Kommunikation muss als interner Kontext erkennbar sein. | Interne Aufrufe enthalten Service-Token oder sind durch interne Netzwerkgrenzen eindeutig geschützt. |

## 4. Fachlicher Kontext und Domänenmodell

Der fachliche Kern besteht aus Kunden, Produkten, Warenkörben, Bestellungen, Beständen, Reservierungen, Zahlungen, Rechnungen und Audit-Snapshots. Jede Entität besitzt eine fachliche Verantwortung und eine technische Datenhoheit.

| Domänenobjekt | Beschreibung | Datenhoheit | Zentrale Zustände |
| --- | --- | --- | --- |
| Product | Verkaufbares Produkt mit Kataloginformationen. | Shop-Service | active, inactive. |
| Basket | Temporäre Produktauswahl eines Kunden. | Shop-Service | open, checked_out, cleared. |
| Order | Fachlicher Bestellauftrag des Kunden. | Shop-Service | CREATED, RESERVATION_PENDING, RESERVED, PAYMENT_PENDING, BOOKING_PENDING, COMPLETED, OUT_OF_STOCK, PAYMENT_FAILED, ROLLBACK_PENDING, ROLLBACK_COMPLETED, FAILED_REQUIRES_MANUAL_REVIEW. |
| WarehouseProduct | Lagerbestand eines Produkts. | Warehouse-Service | available, reserved, blocked. |
| Reservation | Temporäre Blockierung von Bestand für eine Order. | Warehouse-Service | ACTIVE, CANCELLED, BOOKED, REJECTED. |
| Payment | Zahlungsversuch zu einer Order. | Billing-Service | CREATED, PENDING, SUCCEEDED, FAILED, REFUNDED. |
| Invoice | Rechnung zu erfolgreicher Zahlung. | Invoice-Service | REQUESTED, GENERATED, FAILED_RETRYABLE, FAILED_FINAL. |
| AuditSnapshot | Unveränderlicher Nachweis eines Ereignisses oder Zustands. | Audit-Service | append-only. |

### Domänenregeln

| ID | Regel | Prüfbarkeit |
| --- | --- | --- |
| DOM-001 | Eine abgeschlossene Bestellung setzt erfolgreiche Zahlung, finale Lagerbuchung und vollständige Audit-Kette voraus. | E2E-Test prüft Order, Payment, Reservation, Audit und Rechnung. |
| DOM-002 | Eine Bestellung mit Status OUT_OF_STOCK darf keinen erfolgreichen Payment-Datensatz besitzen. | Integrationstest prüft, dass Billing nicht aufgerufen wurde. |
| DOM-003 | Eine aktive Reservierung muss entweder gebucht, storniert oder in eine manuelle Prüfung überführt werden. | Warehouse-Invariantentest prüft keine dauerhaft verwaisten Reservierungen nach Endstatus. |
| DOM-004 | Eine Rechnung darf Zahlungs- und Rechnungsdaten enthalten, aber keine geheimen Payment-Provider-Credentials. | Dokumentenprüfung und Maskierungstest prüfen erlaubte Felder. |

## 5. Systemkontext und Systemgrenzen

Der Shop-Service bildet den einzigen externen Business-API-Einstiegspunkt. Frontends kommunizieren regulär nur mit dem Shop-Service. Warehouse, Billing, Invoice und Audit sind interne Services mit eigener Persistenz. RabbitMQ dient der asynchronen Entkopplung. Redis dient Idempotenz, Session- oder Sperrkoordination. PostgreSQL dient persistenter Datenhaltung pro zustandsbehaftetem Service.

| Grenze | Festlegung | Begründung |
| --- | --- | --- |
| Externe API-Grenze | Öffentliche Business-Aufrufe laufen über den Shop-Service. | Validierung, Autorisierung und Saga-Steuerung bleiben zentral kontrolliert. |
| Interne Service-Grenze | Warehouse, Billing, Invoice und Audit werden nicht direkt von Customer-Frontends angesprochen. | Interne Datenhoheit und Fehlerbehandlung bleiben gekapselt. |
| Datenbank-Grenze | Kein Service liest oder schreibt in Tabellen eines anderen Services. | Versteckte Kopplung und inkonsistente Schreibpfade werden verhindert. |
| Event-Grenze | Asynchrone Folgeprozesse laufen über RabbitMQ mit correlationId. | Rechnungsstellung und Audit können entkoppelt und wiederholbar verarbeitet werden. |
| Demo-Grenze | Simulation-Funktionen sind fachlich Teil des Systems, aber rollen- und umgebungsgebunden. | Fehlerszenarien müssen reproduzierbar sein, dürfen den normalen Kundenpfad aber nicht unkontrolliert beeinflussen. |

## 6. Gesamtanforderungen auf Systemebene

Systemanforderungen gelten serviceübergreifend und sind durch Architektur, Implementierung, Tests und Betriebsnachweise zu erfüllen.

| ID | Anforderung | Nachweis |
| --- | --- | --- |
| SYS-FUNC-001 | Das System muss Bestellungen synchron starten und innerhalb eines fachlich eindeutigen Status zurückgeben. | E2E-Test für 201 COMPLETED, 202 PAYMENT_PENDING, 409 OUT_OF_STOCK und 402 PAYMENT_FAILED. |
| SYS-FUNC-002 | Das System muss alle Bestellschritte über eine gemeinsame correlationId verknüpfen. | Logs, Audit-Timeline und API-Antwort enthalten dieselbe correlationId. |
| SYS-FUNC-003 | Das System muss idempotente Wiederholung kritischer Kommandos unterstützen. | Doppelter Checkout mit gleichem Idempotency-Key erzeugt keine zweite Zahlung und keine zweite Reservierung. |
| SYS-FUNC-004 | Das System muss Kompensationen auslösen, wenn nach lokaler Teilverarbeitung ein späterer Schritt fehlschlägt. | Booking-Fehler führt zu Refund und Status ROLLBACK_COMPLETED. |
| SYS-FUNC-005 | Das System muss für Demo und Abnahme definierte Fehlerzustände auslösen können. | Simulation-Panel erzeugt reproduzierbar Payment-Fehler, Booking-Fehler, Invoice-Fehler und Concurrency-Szenarien. |
| SYS-FUNC-006 | Das System muss technische Fehler als Problem Details mit stabilen Fehlercodes liefern. | API-Contract-Test validiert type, title, status, detail, correlationId und code. |

## 7. Detaillierte funktionale Anforderungen je Subsystem

### Shop-Service

Der Shop-Service verantwortet externe Business-APIs, Authentisierung, Rollenprüfung, Produktkatalog, Warenkorb, Bestellung, Saga-Orchestrierung, Idempotenzannahme und Statusmodell der Order.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-SHOP-001 | Der Shop-Service muss Produktlisten und Produktdetails für Customer und Admin bereitstellen. | Produkte ohne active-Status werden Customer-seitig nicht kaufbar angezeigt. | Customer sieht nur aktive Produkte, Admin kann alle Produkte nach Status filtern. |
| FR-SHOP-002 | Der Shop-Service muss Warenkorbpositionen je Kunde anlegen, ändern, entfernen und anzeigen. | Mengen müssen positive Ganzzahlen sein und Produktreferenzen müssen existieren. | Ungültige Produkt-ID oder Menge kleiner 1 wird mit 400 Problem Details abgelehnt. |
| FR-SHOP-003 | Der Shop-Service muss Checkout über POST /v1/orders mit X-Idempotency-Key verarbeiten. | userId und Idempotency-Key bilden die Idempotenzbasis. | Wiederholung liefert gespeicherte Antwort oder PROCESSING, aber keine Doppelbestellung. |
| FR-SHOP-004 | Der Shop-Service muss beim Checkout eine lokale Order anlegen, bevor externe Schritte gestartet werden. | Order startet mit CREATED und wechselt nach RESERVATION_PENDING. | Audit enthält OrderCreated vor Warehouse-Aufruf. |
| FR-SHOP-005 | Der Shop-Service muss den Warehouse-Service synchron zur Reservierung aufrufen. | Request enthält correlationId, Order-ID, Produktpositionen und Mengen. | Reservierungszusage führt zu RESERVED, Ablehnung zu OUT_OF_STOCK. |
| FR-SHOP-006 | Der Shop-Service muss den Billing-Service synchron zur Zahlungsinitialisierung aufrufen. | Payment-Aufruf erfolgt nur nach erfolgreicher Reservierung. | OUT_OF_STOCK erzeugt keinen Payment-Aufruf. |
| FR-SHOP-007 | Der Shop-Service muss Payment-Pending verarbeiten und Order auf PAYMENT_PENDING setzen. | Bei PENDING darf keine finale Lagerbuchung erfolgen. | Webhook-Fortsetzung kann später BOOKING_PENDING oder ROLLBACK_PENDING auslösen. |
| FR-SHOP-008 | Der Shop-Service muss finale Warehouse-Buchung nach erfolgreichem Payment auslösen. | Booking erfolgt idempotent auf Basis der correlationId. | Erfolgreiches Booking führt zu COMPLETED und leert den Warenkorb. |
| FR-SHOP-009 | Der Shop-Service muss Kompensation auslösen, wenn Payment fehlschlägt. | Aktive Reservierung wird storniert. | Endstatus PAYMENT_FAILED enthält Audit-Einträge PaymentFailed und ReservationCancelled. |
| FR-SHOP-010 | Der Shop-Service muss Refund auslösen, wenn finale Buchung nach erfolgreicher Zahlung fehlschlägt. | Refund erfolgt über Billing und wird mit correlationId verknüpft. | Endstatus ROLLBACK_COMPLETED enthält PaymentRefunded. |
| FR-SHOP-011 | Der Shop-Service muss Order-Statusübergänge zentral validieren. | Nicht erlaubte Übergänge werden verhindert und geloggt. | Unit-Test deckt alle erlaubten und verbotenen Statusübergänge ab. |
| FR-SHOP-012 | Der Shop-Service muss Admin-Lesezugriffe auf Orders, Status, Fehlercodes und Audit-Referenzen bereitstellen. | CUSTOMER darf nur eigene Orders sehen. | Fremdzugriff liefert 403 oder 404 gemäß Datenschutzentscheidung. |

### Warehouse-Service

Der Warehouse-Service verantwortet physischen Bestand, Reservierungen, Reservation Items, finale Buchungen, Wareneingänge, Korrekturen, Concurrency Control und lagerbezogene Fehlerprovokation.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-WHS-001 | Der Warehouse-Service muss verfügbare und reservierte Mengen je Produkt verwalten. | Mengen dürfen nicht negativ werden. | Invariantentest prüft availableQuantity >= 0 und reservedQuantity >= 0. |
| FR-WHS-002 | Der Warehouse-Service muss Reservierungen idempotent über correlationId anlegen. | Gleiche correlationId liefert dieselbe Reservierung oder denselben Ablehnungsstatus. | Wiederholter Reservation-Request verändert Bestände nicht erneut. |
| FR-WHS-003 | Der Warehouse-Service muss Reservierung nur bei ausreichendem Bestand zulassen. | Prüfung erfolgt innerhalb einer lokalen Datenbanktransaktion. | Bestand 0 führt zu REJECTED und Problem Details OUT_OF_STOCK. |
| FR-WHS-004 | Der Warehouse-Service muss pessimistische PostgreSQL-Sperren für konkurrierende Reservierungen nutzen. | Betroffene Produktzeilen werden während Mengenprüfung und Umbuchung gesperrt. | Zwei parallele Bestellungen bei Bestand 1 erzeugen genau eine aktive Reservierung. |
| FR-WHS-005 | Der Warehouse-Service muss Reservierungsstorno idempotent bereitstellen. | Storno ist nur für ACTIVE oder technisch wiederholte CANCELLED-Reservierungen zulässig. | Wiederholter Storno erhöht availableQuantity nicht doppelt. |
| FR-WHS-006 | Der Warehouse-Service muss finale Buchung einer Reservierung idempotent durchführen. | Nur ACTIVE-Reservierungen dürfen nach BOOKED wechseln. | Wiederholtes Booking erzeugt keine zweite Bestandsbewegung. |
| FR-WHS-007 | Der Warehouse-Service muss Wareneingänge und Korrekturbuchungen für LOGISTICS und ADMIN bereitstellen. | Menge, Grund und Benutzerkontext sind Pflicht. | Wareneingang erzeugt StockMovement und Audit-Snapshot. |
| FR-WHS-008 | Der Warehouse-Service muss Fehlerflags für FAIL_NEXT_RESERVATION und FAIL_NEXT_BOOKING unterstützen. | Flags sind nur über Simulation/Admin-Kontext nutzbar. | Demo-Test kann gezielt OUT_OF_STOCK oder Booking-Fehler erzeugen. |
| FR-WHS-009 | Der Warehouse-Service muss jede Bestandsbewegung revisionsfähig speichern. | StockMovement enthält type, quantity, productId, correlationId und actor. | Admin/WMS kann Bewegungen je Produkt nachvollziehen. |

### Billing-Service

Der Billing-Service verantwortet Payment-Fassade, Charge-Erzeugung, Provider-Auswahl, Provider-Stubs, Webhook-Verarbeitung, Refunds, Zahlungsstatus und Payment-Events.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-BIL-001 | Der Billing-Service muss Charges idempotent über correlationId erzeugen. | Pro correlationId darf maximal ein aktiver Charge-Prozess bestehen. | Wiederholter Charge-Aufruf erzeugt keine zweite Provider-Transaktion. |
| FR-BIL-002 | Der Billing-Service muss synchrone Payment-Ergebnisse SUCCEEDED, FAILED und PENDING abbilden. | Provider-spezifische Antworten werden auf ein einheitliches Statusmodell gemappt. | Contract-Test prüft Statusmapping für alle Provider-Stubs. |
| FR-BIL-003 | Der Billing-Service muss Provider-Implementierungen über eine Payment-Fassade kapseln. | Business-Code darf keine provider-spezifische Logik enthalten. | Provider-Wechsel erfolgt über Konfiguration und Adapter. |
| FR-BIL-004 | Der Billing-Service muss Webhooks deduplizieren und verifizieren. | Webhook-ID oder providerReference verhindert doppelte Verarbeitung. | Doppelter Webhook ändert Payment-Status nicht mehrfach. |
| FR-BIL-005 | Der Billing-Service muss PaymentSucceeded und PaymentFailed als Events publizieren. | Events enthalten correlationId, paymentId, orderId, amount, currency und timestamp. | RabbitMQ-Test verifiziert Event-Payload und Routing-Key. |
| FR-BIL-006 | Der Billing-Service muss Refunds idempotent ausführen. | Refund ist nur nach SUCCEEDED zulässig und darf nicht doppelt ausgeführt werden. | Booking-Fehler erzeugt genau einen Refund und Status REFUNDED. |
| FR-BIL-007 | Der Billing-Service muss Payment-Fehler fachlich unterscheidbar machen. | Fehlercodes unterscheiden DECLINED, PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE und INVALID_PAYMENT_STATE. | API und Audit enthalten stabilen Code. |
| FR-BIL-008 | Der Billing-Service muss Demo-Provider für Erfolg, Ablehnung, Pending und Timeout bereitstellen. | Provider-Auswahl ist konfigurierbar. | Simulation-Panel kann den nächsten Payment-Ausgang reproduzierbar setzen. |

### Invoice-Service

Der Invoice-Service verarbeitet PaymentSucceeded-Events asynchron und erstellt Rechnungsartefakte, ohne den erfolgreichen Bestellabschluss fachlich zurückzurollen.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-INV-001 | Der Invoice-Service muss PaymentSucceeded-Events aus RabbitMQ konsumieren. | Event muss correlationId, orderId, paymentId und Rechnungsbasisdaten enthalten. | Event ohne Pflichtfelder wird verworfen oder in eine Dead-Letter-Route geschrieben. |
| FR-INV-002 | Der Invoice-Service muss pro correlationId höchstens eine fachliche Rechnung erzeugen. | invoiceNumber oder correlationId dient als Deduplizierungsbasis. | Wiederholtes Event erzeugt keine zweite Rechnung. |
| FR-INV-003 | Der Invoice-Service muss PDF- oder Dateiartefakte in einem konfigurierten Volume ablegen. | Dateiname enthält invoiceNumber oder correlationId. | Abnahmetest findet Rechnung nach erfolgreicher Bestellung im Volume. |
| FR-INV-004 | Der Invoice-Service muss Fehler retrybar behandeln. | Temporäre Fehler erhöhen Retry-Zähler und öffnen bei Schwelle den Circuit Breaker. | Drei konfigurierte Fehler führen zu FAILED_RETRYABLE oder offenem Circuit Breaker. |
| FR-INV-005 | Der Invoice-Service darf bei Rechnungsfehlern keinen Payment-Refund auslösen. | Invoice-Fehler ist ein Folgeprozessfehler, kein Bestellabschlussfehler. | Order bleibt COMPLETED, Audit zeigt InvoiceGenerated oder InvoiceFailed. |
| FR-INV-006 | Der Invoice-Service muss InvoiceGenerated und CircuitBreakerStateChanged auditierbar machen. | Event enthält Status, Versuchszähler und correlationId. | Admin-Timeline zeigt Rechnungsergebnis und Circuit-Breaker-Wechsel. |

### Audit-Service

Der Audit-Service speichert unveränderliche Snapshots, stellt Timelines bereit und bildet die primäre fachliche Nachvollziehbarkeit für Admin, Demo und Fehleranalyse.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-AUD-001 | Der Audit-Service muss Snapshots append-only speichern. | Update- und Delete-Pfade für Audit-Datensätze sind nicht verfügbar. | Persistenztest bestätigt, dass gespeicherte Snapshots nicht überschrieben werden. |
| FR-AUD-002 | Der Audit-Service muss Snapshots nach correlationId chronologisch abrufbar machen. | Sortierung erfolgt nach occurredAt und stabiler Sequenz. | Admin-Timeline zeigt alle Hauptschritte in korrekter Reihenfolge. |
| FR-AUD-003 | Der Audit-Service muss Events und direkte Snapshot-Annahmen validieren. | Pflichtfelder sind correlationId, eventType, sourceService, occurredAt und payloadVersion. | Ungültiger Snapshot wird abgelehnt und als Validierungsfehler geloggt. |
| FR-AUD-004 | Der Audit-Service muss sensible Felder maskieren. | Tokens, Passwörter, Provider-Secrets und vollständige Zahlungsdaten werden nicht gespeichert. | Maskierungstest findet keine verbotenen Felder im Snapshot-Payload. |
| FR-AUD-005 | Der Audit-Service muss einen SSE- oder Polling-fähigen Timeline-Stream für Admin bereitstellen. | Stream ist rollenbeschränkt und correlationId-filterbar. | Admin Dashboard aktualisiert Timeline ohne manuellen Reload. |
| FR-AUD-006 | Der Audit-Service muss aggregierte Lesemodelle für Demo und Abnahme bereitstellen. | Aggregationen dürfen Audit-Originaldaten nicht verändern. | Admin sieht Statusverteilung und letzte Fehler je Service. |

### Customer Frontend

Die Customer Storefront ermöglicht Produktauswahl, Warenkorbpflege, Checkout und Einsicht in eigene Bestellzustände.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-CUI-001 | Das Customer Frontend muss aktive Produkte such- und filterbar darstellen. | Nicht kaufbare Produkte sind erkennbar und nicht checkoutfähig. | Kunde kann ein aktives Produkt in den Warenkorb legen. |
| FR-CUI-002 | Das Customer Frontend muss Warenkorbpositionen mit Menge, Preis und Gesamtsumme anzeigen. | Mengenänderungen verwenden nur positive Ganzzahlen. | Ungültige Eingabe wird clientseitig verhindert und serverseitig abgesichert. |
| FR-CUI-003 | Das Customer Frontend muss pro Checkout einen stabilen X-Idempotency-Key erzeugen. | Key bleibt für Retry desselben Checkout-Versuchs erhalten. | Browser-Refresh während Checkout erzeugt keine Doppelbestellung. |
| FR-CUI-004 | Das Customer Frontend muss Order-Status verständlich und fachlich korrekt darstellen. | COMPLETED, PAYMENT_PENDING, OUT_OF_STOCK und PAYMENT_FAILED haben unterscheidbare Zustände. | E2E-Test prüft sichtbare Statusmeldungen für vier Szenarien. |
| FR-CUI-005 | Das Customer Frontend darf keine internen Service-Endpunkte direkt aufrufen. | Netzwerkaufrufe gehen regulär an den Shop-Service. | Browser-Test findet keine direkten Calls an Warehouse, Billing, Invoice oder Audit. |

### Admin Frontend

Das Admin Dashboard stellt Bestellübersichten, Timeline, Fehlerzustände, Audit-Suche, Metrik-Verweise und Demo-Unterstützung bereit.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-AUI-001 | Das Admin Frontend muss Bestellungen nach Status, Zeitraum, Kundentyp und correlationId filtern. | Filter dürfen keine unautorisierten Daten ausgeben. | Admin findet eine Demo-Order über correlationId. |
| FR-AUI-002 | Das Admin Frontend muss die vollständige Audit-Timeline je Bestellung darstellen. | Ereignisse werden chronologisch und mit Quellservice angezeigt. | Timeline enthält OrderCreated, ReservationCreated, PaymentSucceeded und StockBooked im Happy Path. |
| FR-AUI-003 | Das Admin Frontend muss Fehlercodes und Kompensationsschritte sichtbar machen. | Fehlerpfade zeigen Ursache, betroffenen Service und Endstatus. | Payment-Fehler zeigt ReservationCancelled und PAYMENT_FAILED. |
| FR-AUI-004 | Das Admin Frontend muss Links oder Hinweise zu Loki/Grafana über correlationId anbieten. | correlationId wird kopierbar und filterbar dargestellt. | Admin kann Logs zur Bestellung eindeutig finden. |
| FR-AUI-005 | Admin-Aktionen müssen rollenbeschränkt und auditierbar sein. | Simulation- oder Reset-Aktionen enthalten actor und reason. | Audit zeigt AdminActionTriggered. |

### Warehouse/WMS Frontend

Die Warehouse/WMS-Ansicht unterstützt Lagerrollen bei Bestand, Reservierung, Wareneingang und Bestandsbewegungen.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-WUI-001 | Das WMS Frontend muss Lagerbestände mit verfügbarer, reservierter und gesperrter Menge anzeigen. | Anzeige basiert auf Warehouse-Daten, nicht auf Shop-Katalogdaten allein. | LOGISTICS sieht Bestand nach Produkt und Status. |
| FR-WUI-002 | Das WMS Frontend muss Wareneingänge erfassen. | Menge, Produkt, Grund und Benutzerkontext sind Pflicht. | Wareneingang erhöht availableQuantity und erzeugt StockMovement. |
| FR-WUI-003 | Das WMS Frontend muss aktive Reservierungen und Buchungen anzeigen. | Filter nach correlationId und Status sind verfügbar. | Lagerrolle findet Reservierung einer Demo-Bestellung. |
| FR-WUI-004 | Das WMS Frontend darf keine Payment- oder Kundengeheimnisse anzeigen. | Payment-Informationen werden maximal als abstrakter Status dargestellt. | Datenschutztest prüft absence sensibler Felder. |

### Simulation/Demo-Control-Panel

Das Simulation-Panel steuert reproduzierbare Demo-Zustände, Fehlerauslösung, Seed-Reset und parallele Szenarien.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-SIM-001 | Das Simulation-Panel muss definierte Szenarien für Happy Path, Payment-Fehler, Out-of-Stock, Booking-Fehler, Invoice-Ausfall und Concurrency starten. | Jedes Szenario setzt kontrolliert die erforderlichen Service-Flags oder Seed-Daten. | Demo-Test kann jedes Szenario ohne manuelle Datenbankänderung auslösen. |
| FR-SIM-002 | Das Simulation-Panel muss Fehlerflags zeitlich begrenzt anwenden. | FAIL_NEXT_* wirkt nur auf den nächsten passenden Prozess oder bis Ablauf. | Ein gesetzter Payment-Fehler beeinflusst nicht unkontrolliert spätere Bestellungen. |
| FR-SIM-003 | Das Simulation-Panel muss Demo-Daten reproduzierbar zurücksetzen können. | Reset ist rollenbeschränkt und auditierbar. | Nach Reset sind definierte Produkte, Bestände und Nutzer vorhanden. |
| FR-SIM-004 | Das Simulation-Panel muss parallele Bestellungen für Concurrency-Tests starten können. | Requests nutzen unterschiedliche correlationIds und kontrollierte Idempotency-Keys. | Bei Bestand 1 wird genau eine Order fortgesetzt. |

### Infrastruktur- und Plattformumgebung

Die Plattform stellt lokale Reproduzierbarkeit, Service-Start, Netzwerke, Persistenz, Broker, Cache, Logging und Konfiguration bereit.

| ID | Anforderung | Validierung und Regeln | Akzeptanzkriterium |
| --- | --- | --- | --- |
| FR-PLT-001 | Die lokale Umgebung muss über Docker Compose startbar sein. | Services, Datenbanken, Redis, RabbitMQ und Observability-Komponenten sind definiert. | Ein dokumentierter Startbefehl bringt das System in lauffähigen Zustand. |
| FR-PLT-002 | Jeder zustandsbehaftete Service muss eigene PostgreSQL-Persistenz besitzen. | Datenbanknamen, Nutzer und Verbindungsstrings sind servicebezogen. | Kein Service nutzt Tabellen eines anderen Services. |
| FR-PLT-003 | RabbitMQ muss Queues, Exchanges und Dead-Letter-Pfade für Events bereitstellen. | Kritische Events können wiederholt oder separat analysiert werden. | Fehlgeschlagene Invoice-Verarbeitung landet nicht unkontrolliert verloren. |
| FR-PLT-004 | Redis muss für Idempotenz- und Sperrkoordinierung verfügbar sein. | TTLs und gespeicherte Antworten sind konfigurierbar. | Idempotenztest besteht auch bei parallelen Checkout-Requests. |
| FR-PLT-005 | Konfiguration muss über Umgebungsvariablen erfolgen. | Secrets dürfen nicht fest im Code stehen. | .env.example dokumentiert erforderliche Variablen ohne echte Secrets. |

## 8. Detaillierte nichtfunktionale Anforderungen je Qualitätsbereich

| ID | Qualitätsbereich | Anforderung | Mess- oder Prüfkriterium |
| --- | --- | --- | --- |
| NFR-PERF-001 | Performance | Der synchrone Happy Path muss lokal unter normaler Demo-Last innerhalb von 3 Sekunden eine fachliche Antwort liefern. | E2E-Messung über 20 Läufe zeigt p95 kleiner 3 Sekunden ohne Invoice-Wartezeit. |
| NFR-PERF-002 | Performance | Listenendpunkte müssen paginiert oder begrenzt abrufbar sein. | Admin-Orderliste akzeptiert limit und offset oder cursor. |
| NFR-SCAL-001 | Skalierbarkeit | Services müssen horizontal skalierbar entworfen sein, soweit keine lokalen In-Memory-Zustände erforderlich sind. | Idempotenz, Saga-Zustand und Sessions liegen in Redis oder PostgreSQL. |
| NFR-AVL-001 | Verfügbarkeit | Ausfall des Invoice-Service darf den erfolgreichen Checkout fachlich nicht zurückrollen. | Invoice-Ausfall-Szenario endet mit Order COMPLETED und Invoice-Warnung. |
| NFR-ROB-001 | Robustheit | Service-Aufrufe müssen Timeouts und kontrollierte Fehlerbehandlung besitzen. | Integrationstests simulieren Timeout für Warehouse, Billing und Invoice. |
| NFR-FT-001 | Fehlertoleranz | Asynchrone Eventverarbeitung muss Retry und Dead-Letter-Behandlung unterstützen. | Fehlgeschlagene Eventverarbeitung ist sichtbar und erneut behandelbar. |
| NFR-IDEM-001 | Idempotenz | Kritische Kommandos müssen wiederholbar sein, ohne Seiteneffekte doppelt auszuführen. | Tests für Order, Reservation, Booking, Charge, Refund und Invoice bestehen. |
| NFR-CON-001 | Nebenläufigkeit | Warehouse muss Überverkäufe bei parallelen Reservierungen verhindern. | Concurrency-Test mit Bestand 1 erzeugt keine negative Menge. |
| NFR-SEC-001 | Authentisierung | Externe geschützte APIs müssen JWT oder vergleichbare Tokens validieren. | Request ohne gültiges Token wird abgelehnt. |
| NFR-SEC-002 | Autorisierung | Rollen müssen serverseitig erzwungen werden. | Clientseitige Navigation allein ist kein Sicherheitsmechanismus. |
| NFR-TRACE-001 | Nachvollziehbarkeit | Jede fachlich relevante Aktion muss correlationId, actor und sourceService enthalten. | Log- und Audit-Prüfung finden diese Felder in Hauptpfaden. |
| NFR-MAINT-001 | Wartbarkeit | Fachlogik, Infrastrukturadapter und API-Schicht müssen in klaren Modulen getrennt sein. | Code-Review kann Verantwortlichkeiten je Modul nachvollziehen. |
| NFR-EXT-001 | Erweiterbarkeit | Payment-Provider müssen durch Adapter erweiterbar sein. | Neuer Stub kann ohne Änderung am Order-Orchestrator registriert werden. |
| NFR-TEST-001 | Testbarkeit | Jeder Haupt- und Fehlerpfad muss automatisiert oder reproduzierbar nachweisbar sein. | Testmatrix deckt alle definierten Demo-Szenarien ab. |
| NFR-OBS-001 | Beobachtbarkeit | Logs, Metriken und Audit müssen eine Bestellung serviceübergreifend rekonstruierbar machen. | correlationId-Suche zeigt zusammenhängende Kette. |
| NFR-UX-001 | Bedienbarkeit | Frontends müssen Status, Fehler und nächste fachliche Handlung klar anzeigen. | Usability-Check prüft sichtbare Zustände für Pending, Failed und Completed. |
| NFR-REP-001 | Reproduzierbarkeit | Laufzeitumgebung und Demo-Daten müssen reproduzierbar start- und rücksetzbar sein. | Docker Compose plus Seed erzeugt definierte Ausgangslage. |

## 9. End-to-End-Prozessanforderungen

Der End-to-End-Prozess beginnt mit einem gefüllten Warenkorb und endet mit einem fachlichen Endstatus. Der Shop-Service koordiniert alle synchronen Entscheidungen und löst asynchrone Folgeprozesse aus.

| Schritt | Verantwortlich | Vorbedingung | Nachbedingung | Sichtbarkeit |
| --- | --- | --- | --- | --- |
| Checkout starten | Customer Frontend, Shop | Warenkorb enthält kaufbare Produkte und Idempotency-Key. | Order CREATED. | Log und Audit OrderCreated. |
| Bestand reservieren | Shop, Warehouse | Order RESERVATION_PENDING. | Reservation ACTIVE oder REJECTED. | Warehouse-Log, Audit ReservationCreated oder ReservationRejected. |
| Zahlung starten | Shop, Billing | Reservation ACTIVE. | Payment SUCCEEDED, FAILED oder PENDING. | Billing-Log, Payment-Event, Audit. |
| Pending fortsetzen | Billing, Shop | Payment PENDING. | Booking oder Rollback wird gestartet. | Webhook-Log und OrderStatusChanged. |
| Final buchen | Shop, Warehouse | Payment SUCCEEDED. | Reservation BOOKED. | StockBooked und OrderStatusChanged. |
| Rechnung erzeugen | Billing, RabbitMQ, Invoice | PaymentSucceeded-Event. | Invoice GENERATED oder retrybarer Fehler. | InvoiceGenerated oder InvoiceFailed. |
| Order abschließen | Shop | Booking erfolgreich. | Order COMPLETED. | Audit OrderCompleted und Metrik. |

### End-to-End-Anforderungen

| ID | Anforderung | Akzeptanzkriterium |
| --- | --- | --- |
| E2E-ORD-001 | Happy Path muss Order, Reservation, Payment, Booking, Invoice und Audit vollständig verbinden. | Demo-Szenario 1 erfüllt alle Abnahmekriterien ohne manuelle Eingriffe. |
| E2E-ORD-002 | Payment-Pending muss die Order pausieren, ohne Bestand final auszubuchen. | Während PAYMENT_PENDING existiert ACTIVE Reservation und kein StockBooked. |
| E2E-ORD-003 | Jeder Endstatus muss fachlich eindeutig und operativ interpretierbar sein. | Endstatus gehört zu COMPLETED, OUT_OF_STOCK, PAYMENT_FAILED, ROLLBACK_COMPLETED oder FAILED_REQUIRES_MANUAL_REVIEW. |
| E2E-ORD-004 | Jeder Fehlerpfad muss dem Kunden und Admin konsistente Informationen liefern. | Customer sieht fachliche Kurzmeldung, Admin sieht technische Ursache und correlationId. |

## 10. Fehler-, Ausnahme- und Kompensationsanforderungen

Fehlerbehandlung ist Bestandteil des fachlichen Designs. Jede Kompensation muss idempotent, auditierbar und fachlich begründet sein.

| Fehlerfall | Auslöser | Kompensation | Endstatus | Pflichtnachweis |
| --- | --- | --- | --- | --- |
| Lager nicht ausreichend | Reservation abgelehnt. | Keine Folgekompensation, da kein Payment gestartet wurde. | OUT_OF_STOCK. | Audit ReservationRejected und OrderFailedOutOfStock. |
| Payment abgelehnt | Billing liefert FAILED. | Reservation stornieren. | PAYMENT_FAILED. | PaymentFailed und ReservationCancelled. |
| Payment-Timeout | Billing-Aufruf unklar. | Payment-Status prüfen oder idempotent wiederholen. | PAYMENT_PENDING oder technischer Fehlerstatus. | Timeout-Log mit correlationId. |
| Webhook meldet Failure | Pending-Payment endet negativ. | Reservation stornieren. | PAYMENT_FAILED. | WebhookReceived und ReservationCancelled. |
| Booking schlägt fehl | Zahlung erfolgreich, Warehouse-Booking fehlerhaft. | Refund auslösen. | ROLLBACK_COMPLETED oder FAILED_REQUIRES_MANUAL_REVIEW. | PaymentRefunded oder RefundFailed. |
| Invoice fällt aus | Rechnungserstellung fehlerhaft. | Retry, Circuit Breaker, kein Payment-Rollback. | Order bleibt COMPLETED. | InvoiceFailed und CircuitBreakerStateChanged. |
| Audit temporär nicht erreichbar | Snapshot-Annahme fehlerhaft. | Retry oder lokale Fehlerprotokollierung. | Fachprozess wird nicht unkontrolliert blockiert. | Error-Log mit eventType und correlationId. |

| ID | Anforderung | Akzeptanzkriterium |
| --- | --- | --- |
| ERR-COMP-001 | Kompensationen müssen denselben correlationId-Kontext wie die ursprüngliche Order verwenden. | Audit-Timeline zeigt Ursache und Kompensation in einer Kette. |
| ERR-COMP-002 | Kompensationsendpunkte müssen idempotent sein. | Wiederholter Reservation-Cancel oder Refund verändert den Zustand nicht doppelt. |
| ERR-COMP-003 | Scheiternde Kompensation muss in manuelle Prüfung überführt werden. | Endstatus FAILED_REQUIRES_MANUAL_REVIEW enthält Fehlerursache und nächsten operativen Schritt. |
| ERR-COMP-004 | Technische Ausnahmen müssen als Problem Details zurückgegeben werden, sofern ein HTTP-Kontext besteht. | Fehlerantwort enthält status, code und correlationId. |

## 11. Schnittstellen- und Kommunikationsanforderungen

Die Kommunikation nutzt REST für synchrone Entscheidungen und RabbitMQ für asynchrone Folgeprozesse. Alle Schnittstellen müssen versioniert, validiert und über correlationId nachvollziehbar sein.

### REST-Anforderungen

| ID | Schnittstelle | Anforderung | Akzeptanzkriterium |
| --- | --- | --- | --- |
| INT-REST-001 | Frontend zu Shop | Alle Frontends müssen regulär über versionierte Shop-APIs kommunizieren. | Pfade beginnen mit /v1 oder einer dokumentierten Version. |
| INT-REST-002 | Shop zu Warehouse | Reservation, Cancel und Booking müssen REST-Contracts mit correlationId verwenden. | Contract-Test prüft Request und Response. |
| INT-REST-003 | Shop zu Billing | Charge und Refund müssen idempotente REST-Kommandos sein. | Gleiche correlationId erzeugt keinen doppelten Charge oder Refund. |
| INT-REST-004 | Fehlerformat | Fehlerantworten müssen RFC-7807-kompatible Problem Details nutzen. | Schema enthält type, title, status, detail, code und correlationId. |
| INT-REST-005 | Header | X-Correlation-Id muss bei jedem internen und externen fachlichen Aufruf weitergegeben werden. | Trace-Test findet durchgängige correlationId. |

### Event-Anforderungen

| ID | Event | Publisher | Consumer | Anforderung |
| --- | --- | --- | --- | --- |
| INT-EVT-001 | OrderStatusChanged | Shop-Service | Audit-Service | Jeder fachliche Statuswechsel der Order wird publiziert oder auditierbar übergeben. |
| INT-EVT-002 | ReservationCreated | Warehouse-Service | Audit-Service | Erfolgreiche Reservierung wird mit Produktpositionen und Mengen dokumentiert. |
| INT-EVT-003 | ReservationCancelled | Warehouse-Service | Audit-Service | Storno enthält Ursache und ursprüngliche correlationId. |
| INT-EVT-004 | StockBooked | Warehouse-Service | Audit-Service | Finale Buchung enthält Reservation-ID und Mengen. |
| INT-EVT-005 | PaymentSucceeded | Billing-Service | Invoice-Service, Audit-Service | Erfolgreiche Zahlung löst Rechnung und Audit aus. |
| INT-EVT-006 | PaymentFailed | Billing-Service | Audit-Service | Fehlgeschlagene Zahlung ist fachlich unterscheidbar. |
| INT-EVT-007 | PaymentRefunded | Billing-Service | Audit-Service | Refund enthält Bezug zur ursprünglichen Zahlung. |
| INT-EVT-008 | InvoiceGenerated | Invoice-Service | Audit-Service | Rechnungserstellung wird mit invoiceNumber und Artefaktreferenz dokumentiert. |
| INT-EVT-009 | CircuitBreakerStateChanged | Invoice-Service | Audit-Service | Resilienzstatus wird für Demo und Betrieb sichtbar. |

## 12. Daten-, Persistenz- und Konsistenzanforderungen

Jeder Service besitzt eigene Persistenz und ist für Konsistenz seiner lokalen Daten verantwortlich. Serviceübergreifende Konsistenz entsteht über Saga-Schritte, idempotente Kommandos, Events und Kompensation.

| ID | Anforderung | Akzeptanzkriterium |
| --- | --- | --- |
| DATA-OWN-001 | Der Shop-Service besitzt Orders, Order Items, Baskets, Products aus Shop-Sicht, Users und Rollen. | Keine Warehouse- oder Billing-Tabellen im Shop-Schema. |
| DATA-OWN-002 | Der Warehouse-Service besitzt Warehouse Products, Reservations, Reservation Items und Stock Movements. | Bestandsänderungen erfolgen nur über Warehouse-APIs oder interne Warehouse-Logik. |
| DATA-OWN-003 | Der Billing-Service besitzt Payments, Provider References, Refunds und Webhook-Deduplizierung. | Shop speichert keine geheimen Payment-Providerdaten. |
| DATA-OWN-004 | Der Invoice-Service besitzt Rechnungsartefakte und Generierungsstatus. | Rechnung kann über invoiceNumber oder correlationId gefunden werden. |
| DATA-OWN-005 | Der Audit-Service besitzt Snapshots und Lesemodelle ohne Business-Schreibentscheidungen. | Audit verändert keine Order-, Payment- oder Warehouse-Zustände. |
| DATA-CONS-001 | Lokale Transaktionen müssen alle zusammengehörigen lokalen Änderungen atomar speichern. | Warehouse reserviert Bestand und Reservation innerhalb einer Transaktion. |
| DATA-CONS-002 | Serviceübergreifende Zustände müssen über Endstatus interpretierbar sein. | Es gibt keine Order ohne fachlich interpretierbaren End- oder Zwischenstatus. |
| DATA-CONS-003 | Idempotenzdaten müssen eine TTL oder definierte Aufbewahrungsdauer besitzen. | Wiederholung innerhalb TTL liefert konsistente Antwort. |
| DATA-CONS-004 | Auditdaten müssen länger aufbewahrt werden als operative Idempotenzlocks. | Audit-Timeline bleibt nach Abschluss abrufbar. |

## 13. Sicherheits-, Datenschutz- und Betriebsanforderungen

Sicherheit wird serverseitig durch Authentisierung, Autorisierung, Eingabevalidierung, Geheimnisschutz, Fehlerformat, Netzwerktrennung und Auditierbarkeit durchgesetzt.

| ID | Bereich | Anforderung | Akzeptanzkriterium |
| --- | --- | --- | --- |
| SEC-AUTH-001 | Authentisierung | Geschützte APIs müssen gültige Tokens validieren. | Request ohne Token erhält 401. |
| SEC-AUTHZ-001 | Autorisierung | Rollenbasierte Berechtigungen müssen pro Endpoint erzwungen werden. | CUSTOMER kann keine Admin- oder Simulation-Endpunkte nutzen. |
| SEC-VAL-001 | Validierung | Alle externen Eingaben müssen DTO-validiert werden. | Ungültige Payload erzeugt 400 mit Feldhinweis. |
| SEC-PRIV-001 | Datenschutz | Personen- und Zahlungsdaten müssen minimal gespeichert und in Logs maskiert werden. | Logprüfung findet keine Passwörter, Tokens oder vollständigen Zahlungsdaten. |
| SEC-SECRET-001 | Secrets | Secrets müssen über Umgebung oder Secret-Mechanismus konfiguriert werden. | Keine echten Secrets im Repository. |
| SEC-NET-001 | Netzwerk | Datenbanken, RabbitMQ und interne Services dürfen nicht unnötig öffentlich exponiert werden. | Docker Compose veröffentlicht nur erforderliche Ports. |
| OPS-BOOT-001 | Betrieb | Services müssen Healthchecks bereitstellen. | Compose kann Startreihenfolge und Verfügbarkeit prüfen. |
| OPS-CONF-001 | Konfiguration | Umgebung muss mit dokumentierten Variablen reproduzierbar konfigurierbar sein. | .env.example ist vollständig und enthält keine echten Secrets. |
| OPS-REC-001 | Recovery | Demo-Daten müssen rücksetzbar sein, ohne manuelle Tabellenbearbeitung. | Reset-Szenario stellt definierte Ausgangslage wieder her. |

## 14. Observability-, Logging- und Audit-Anforderungen

Observability muss fachliche und technische Diagnose ermöglichen. Logs, Metriken und Audit-Snapshots erfüllen unterschiedliche Zwecke und dürfen nicht gegeneinander ersetzt werden.

| ID | Bereich | Anforderung | Akzeptanzkriterium |
| --- | --- | --- | --- |
| OPS-OBS-001 | Logging | Jeder Service muss strukturierte JSON-Logs erzeugen. | Logeintrag enthält timestamp, level, service, message und correlationId. |
| OPS-OBS-002 | Correlation | correlationId muss über Frontend, Shop, Warehouse, Billing, RabbitMQ, Invoice und Audit hinweg erhalten bleiben. | Grafana/Loki-Suche rekonstruiert Bestellkette. |
| OPS-OBS-003 | Metriken | Services müssen technische und fachliche Metriken bereitstellen oder ableitbar loggen. | Dashboard zeigt Bestellanzahl, Fehlerrate, Payment-Ergebnisse und Invoice-Fehler. |
| OPS-OBS-004 | Audit | Fachlich relevante Zustandswechsel müssen als Audit-Snapshots verfügbar sein. | Admin-Timeline zeigt mindestens alle Hauptschritte des Bestellprozesses. |
| OPS-OBS-005 | Fehlerdiagnose | Fehlerlogs müssen service, operation, code, correlationId und stack oder cause enthalten. | Simulierter Fehler ist eindeutig lokalisierbar. |
| OPS-OBS-006 | Datenschutz | Logs und Audit müssen sensible Felder maskieren. | Automatischer Test prüft verbotene Schlüssel. |
| OPS-OBS-007 | Demo | Demo-Szenarien müssen sichtbar machen, warum ein Endstatus entstanden ist. | Timeline erklärt Payment-Fehler, Out-of-Stock, Refund oder Invoice-Ausfall. |

## 15. Frontend- und UX-bezogene Anforderungen

Die Frontends dienen nicht nur als Bedienoberfläche, sondern auch als Sichtbarkeitsschicht für Status, Fehler, Timelines und Demo-Nachweise.

| ID | Bereich | Anforderung | Akzeptanzkriterium |
| --- | --- | --- | --- |
| UX-CUS-001 | Customer | Checkout darf während laufender Verarbeitung nicht mehrfach unkontrolliert ausgelöst werden. | Button zeigt laufenden Zustand und nutzt denselben Idempotency-Key für Retry. |
| UX-CUS-002 | Customer | Fehler müssen fachlich verständlich und ohne interne Details angezeigt werden. | OUT_OF_STOCK und PAYMENT_FAILED haben klare Kundenmeldung. |
| UX-ADM-001 | Admin | Admin muss correlationId, Statushistorie und Fehlerursache auf einer Detailseite sehen. | Ein Klick von Orderliste öffnet Timeline. |
| UX-ADM-002 | Admin | Audit- und Log-Verweise müssen kopierbar oder direkt nutzbar sein. | correlationId kann aus UI kopiert werden. |
| UX-WMS-001 | WMS | Lageraktionen müssen vor Ausführung validiert und nach Ausführung sichtbar bestätigt werden. | Wareneingang zeigt aktualisierte Mengen und Movement. |
| UX-SIM-001 | Simulation | Demo-Steuerung muss aktive Fehlerflags, nächste Wirkung und Reset-Zustand anzeigen. | Operator erkennt, welches Szenario als nächstes beeinflusst wird. |
| UX-ACC-001 | Bedienbarkeit | Alle Hauptfunktionen müssen per Tastatur erreichbar und visuell unterscheidbar sein. | Manuelle Prüfung bestätigt Fokuszustände und Formularlabels. |

## 16. Test-, Abnahme- und Nachweisanforderungen

Tests müssen Anforderungen, Architekturversprechen und Demo-Fähigkeit nachweisen. Die Teststrategie umfasst Unit-, Integration-, Contract-, E2E-, Concurrency- und Demo-Tests.

| ID | Testebene | Anforderung | Nachweis |
| --- | --- | --- | --- |
| TST-UNIT-001 | Unit | Statusmaschinen und Entscheidungslogik müssen isoliert getestet werden. | Tests für Order, Payment, Reservation und Invoice-Status. |
| TST-INT-001 | Integration | Services müssen mit Persistenz und Broker getestet werden. | Warehouse-Locking, Billing-Webhook und Audit-Persistenz bestehen. |
| TST-CON-001 | Contract | REST- und Event-Payloads zwischen Services müssen vertraglich abgesichert sein. | Contract Tests für Shop-Warehouse, Shop-Billing und PaymentSucceeded. |
| TST-E2E-001 | E2E | Happy Path muss vollständige Bestellung prüfen. | Order COMPLETED, Payment SUCCEEDED, Reservation BOOKED, Rechnung vorhanden, Audit vollständig. |
| TST-E2E-002 | E2E | Payment-Fehler muss Reservierung kompensieren. | Keine aktive Reservierung und Order PAYMENT_FAILED. |
| TST-E2E-003 | E2E | Out-of-Stock darf Billing nicht aufrufen. | Kein Payment-Datensatz und Order OUT_OF_STOCK. |
| TST-E2E-004 | E2E | Booking-Fehler muss Refund auslösen. | Payment REFUNDED und Order ROLLBACK_COMPLETED. |
| TST-E2E-005 | E2E | Invoice-Ausfall darf Order nicht zurückrollen. | Order COMPLETED und Invoice-Fehler auditierbar. |
| TST-CONC-001 | Concurrency | Parallele Reservierungen müssen Überverkauf verhindern. | Bestand wird nicht negativ, genau eine Order wird fortgesetzt. |
| TST-DEMO-001 | Demo | Simulation-Szenarien müssen reproduzierbar ausführbar sein. | Demo-Skript kann alle Szenarien in definierter Reihenfolge auslösen. |

## 17. Risiko-, Einschränkungs- und Nicht-Ziel-Bereich

| ID | Risiko oder Einschränkung | Auswirkung | Gegenmaßnahme |
| --- | --- | --- | --- |
| RSK-001 | Webhook-Fortsetzung kann komplexe Zwischenzustände erzeugen. | Pending-Sagas können hängen bleiben. | Statusabfrage, Retry, Audit und manuelle Prüfung vorsehen. |
| RSK-002 | Concurrency-Tests können ohne echte DB-Sperren instabil werden. | Überverkauf wird nicht zuverlässig verhindert. | PostgreSQL-Transaktionen mit SELECT FOR UPDATE verwenden. |
| RSK-003 | Audit-Payloads können zu groß oder sensibel werden. | Speicher- und Datenschutzrisiken. | Versionierte, maskierte und begrenzte Payloads definieren. |
| RSK-004 | Zu viele Frontend-Funktionen können Kernprozess verzögern. | Demo zeigt UI, aber nicht Architekturversprechen. | Admin, Simulation und Customer-Checkout priorisieren. |
| RSK-005 | Docker-Startreihenfolge kann lokale Demo stören. | Services starten instabil. | Healthchecks, Retry beim Boot und dokumentierter Startablauf. |
| NZ-001 | Echte Zahlungsanbieterintegration ist kein Ziel. | Keine produktive Zahlungsabwicklung. | Provider-Stubs bilden fachliche Zustände realitätsnah ab. |
| NZ-002 | Produktive Compliance-Zertifizierung ist kein Ziel. | Keine Freigabe für echte Zahlungsdaten. | Sicherheitsmechanismen werden fachlich demonstriert. |
| NZ-003 | Globale Hochverfügbarkeit ist kein Ziel. | Lokaler Demo-Betrieb steht im Vordergrund. | Architektur bleibt grundsätzlich skalierbar, aber lokal betreibbar. |

## 18. Zusammenfassende Anforderungsmatrix

| Kategorie | Kennungsbereich | Primäre Subsysteme | Prüfnachweis |
| --- | --- | --- | --- |
| Systemziele | SYS-GOAL, SYS-FUNC | Alle Services und Frontends | Architekturreview, E2E-Test, Demo. |
| Rollen und Security | SEC-RBAC, SEC-AUTH, SEC-AUTHZ, SEC-VAL | Shop, Frontends, Plattform | Auth-Tests, Rollenmatrix, Security-Review. |
| Fachfunktionen | FR-SHOP, FR-WHS, FR-BIL, FR-INV, FR-AUD | Backend-Services | Unit-, Integration- und Contract-Tests. |
| Frontend-Funktionen | FR-CUI, FR-AUI, FR-WUI, FR-SIM, UX | React-Frontends | UI/E2E-Tests, manuelle Abnahme. |
| Kommunikation | INT-REST, INT-EVT | Shop, Warehouse, Billing, Invoice, Audit, RabbitMQ | Contract Tests, Event Tests, Trace-Prüfung. |
| Daten und Konsistenz | DATA-OWN, DATA-CONS | Alle zustandsbehafteten Services | Schema-Review, Invariantentests, Concurrency-Test. |
| Nichtfunktional | NFR | Alle Subsysteme | Performance-, Resilienz-, Observability- und Testbarkeitsnachweise. |
| Betrieb und Observability | OPS | Plattform, alle Services, Admin | Healthchecks, Logs, Dashboards, Audit-Timeline. |
| Tests und Abnahme | TST | Gesamtsystem | Automatisierte Tests und Demo-Skript. |
| Risiken und Nicht-Ziele | RSK, NZ | Projekt und Architektur | Review, Priorisierung, Abnahmeprotokoll. |

### Abschlusskriterien

| ID | Kriterium | Erfüllungsnachweis |
| --- | --- | --- |
| ACC-001 | Alle Muss-Funktionen des Bestellprozesses sind implementiert und über die UI oder API ausführbar. | Happy-Path-E2E-Test und Demo-Durchlauf. |
| ACC-002 | Alle definierten Fehler- und Kompensationspfade sind reproduzierbar. | Simulation-Panel und E2E-Fehlerpfadtests. |
| ACC-003 | Audit, Logs und Metriken erlauben die Rekonstruktion jeder Demo-Bestellung. | correlationId-Prüfung in Admin, Audit und Loki/Grafana. |
| ACC-004 | Rollen, Sicherheitsgrenzen und Datenhoheit sind technisch umgesetzt. | Security-Test, Code-Review und Architekturreview. |
| ACC-005 | Lokaler Betrieb ist reproduzierbar start-, test- und rücksetzbar. | Docker-Compose-Start, Seed-Reset und dokumentierter Demo-Ablauf. |
