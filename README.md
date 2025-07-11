# PV-Protokoll-System

## Projektbeschreibung

Das PV-Protokoll-System ist eine webbasierte SaaS-Lösung für Installateure von Photovoltaik-Anlagen. Es digitalisiert die Abläufe rund um Anlagenverwaltung, Protokollierung, Aufgabenmanagement, Benutzerverwaltung und Dokumentenmanagement. Die Anwendung ist für den produktiven Einsatz auf einem eigenen Server (VPS) konzipiert und legt besonderen Wert auf Sicherheit und Datenschutz.

---

## 🚀 Aktuelle Features & Verbesserungen

### ✅ **Vollständig implementiert:**
- **Moderne UI/UX**: Bootstrap 5, responsive Design, deutsche Lokalisierung
- **Benutzerverwaltung**: Rollen (Admin, Techniker, Kunde), sichere Authentifizierung
- **Anlagenverwaltung**: Kunden, PV-Anlagen, Bild-Upload, Kartenintegration
- **Protokollsystem**: Vorlagen-Editor, dynamische Formulare, PDF-Export
- **Aufgabenmanagement**: Zuweisung, Deadlines, Status-Tracking
- **Sicherheit**: CSRF-Schutz, sichere Uploads, Logging, Passwort-Validierung
- **Automatische Tests**: Selenium-Tests nach jedem Serverstart
- **Mandantenfähigkeit**: Company-basierte Datenisolation

### 🔧 **Technische Verbesserungen:**
- **PDF-Export**: WeasyPrint mit Fallback-Mechanismus
- **Error-Handling**: Graceful Degradation bei fehlenden Bibliotheken
- **Performance**: Optimierte Datenbankabfragen, Caching
- **Monitoring**: Prometheus-Metriken, Sentry-Integration (optional)

---

## Features
- **Benutzerverwaltung** mit Rollen (Admin, Techniker, Kunde)
- **Login, Logout, Passwort-Reset** (Django-Standard, sicher)
- **Anlagenverwaltung** (Anlegen, Bearbeiten, Löschen, Gruppieren, Kartenansicht)
- **Kundenverwaltung**
- **Aufgabenmanagement** (Erstellen, Zuweisen, Deadlines)
- **Protokollsystem** (Vorlagen, digitale Unterschrift, PDF-Export)
- **Datei-Upload** (Bilder, Protokolle, Dokumente, 20MB-Limit, erlaubte Dateitypen)
- **SaaS-Payment (Dummy)**
- **Responsive Design** (mobil nutzbar)
- **Admin-Backend** (nur für Admins)
- **REST-API (optional, vorbereitet)**
- **Automatische Tests** (Selenium nach Serverstart)

---

## Sicherheitsfeatures
- Sichere Passwortspeicherung (PBKDF2, Salt, starke Validatoren)
- Sichere Datei-Uploads (Größenlimit, erlaubte Dateitypen, Speicherort außerhalb Webroot)
- Benutzer- und Rechteverwaltung (Rollen, Permissions, Zugriffsbeschränkungen)
- Logging sicherheitsrelevanter Ereignisse (`django-security.log`)
- Sichere Authentifizierung (Login, Logout, Passwort-Reset)
- CSRF-Schutz, Secure Cookies, HSTS, X-Frame-Options, XSS-Filter
- Nutzung von Umgebungsvariablen für alle Secrets
- WhiteNoise für statische Dateien in Produktion
- Hinweise zu 2FA und Rate-Limit (siehe unten)

---

## Installationsanleitung (lokal & Produktion)

### Voraussetzungen
- Python 3.10+
- pip, venv
- (Für Produktion empfohlen: PostgreSQL, Nginx, Gunicorn)
- **Für PDF-Export (WeasyPrint) auf macOS:**
  - Folgende Bibliotheken müssen mit Homebrew installiert werden:
    ```sh
    brew install cairo pango gdk-pixbuf libffi gobject-introspection gtk+3
    ```
  - Danach müssen folgende Umgebungsvariablen gesetzt werden (vor jedem Serverstart oder dauerhaft in ~/.zshrc):
    ```sh
    export LDFLAGS="-L/opt/homebrew/opt/libffi/lib -L/opt/homebrew/opt/cairo/lib -L/opt/homebrew/opt/pango/lib -L/opt/homebrew/opt/gdk-pixbuf/lib"
    export CPPFLAGS="-I/opt/homebrew/opt/libffi/include -I/opt/homebrew/opt/cairo/include -I/opt/homebrew/opt/pango/include -I/opt/homebrew/opt/gdk-pixbuf/include"
    export PKG_CONFIG_PATH="/opt/homebrew/opt/libffi/lib/pkgconfig:/opt/homebrew/opt/cairo/lib/pkgconfig:/opt/homebrew/opt/pango/lib/pkgconfig:/opt/homebrew/opt/gdk-pixbuf/lib/pkgconfig"
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/opt/homebrew/opt/libffi/lib:/opt/homebrew/opt/cairo/lib:/opt/homebrew/opt/pango/lib:/opt/homebrew/opt/gdk-pixbuf/lib"
    ```
  - **Hinweis**: Ohne diese Schritte funktioniert der PDF-Export nicht, aber die Anwendung läuft trotzdem mit HTML-Fallback!

### 1. Repository klonen & Umgebung einrichten
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# .env anpassen (SECRET_KEY, DB, ALLOWED_HOSTS, ...)
```

### 2. Migrationen & Superuser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 3. Entwicklung starten
```bash
python manage.py runserver
```
**Hinweis**: Automatische Selenium-Tests werden nach dem Serverstart ausgeführt!

### 4. Produktion (Beispiel)
- Gunicorn: `gunicorn pv_protocol.wsgi:application`
- Nginx als Reverse Proxy (HTTPS!)
- WhiteNoise für statische Dateien
- Datenbank: PostgreSQL empfohlen
- `.env` mit echten Secrets und Produktionsdaten füllen

---

## 🧪 Automatische Tests

Das System führt nach jedem Serverstart automatisch Selenium-Tests durch:

```bash
python manage.py runserver
# Automatische Tests werden nach 3 Sekunden gestartet
```

**Getestete Funktionen:**
- ✅ Login/Logout
- ✅ Dashboard-Zugriff
- ✅ Protokoll-Liste
- ✅ Protokoll-Erstellung
- ⚠️ PDF-Export (abhängig von WeasyPrint-Installation)

---

## 📊 Monitoring & Logging

### Automatische Tests
- Selenium-Tests nach jedem Serverstart
- Validierung der Kernfunktionen
- Detaillierte Fehlerberichte

### Logging
- Sicherheitsrelevante Ereignisse: `django-security.log`
- Benutzer-Aktionen und System-Events
- Error-Tracking (optional mit Sentry)

### Performance-Monitoring
- Prometheus-Metriken verfügbar
- `/metrics` Endpoint für Monitoring
- Datenbank-Performance-Tracking

---

## 🔧 Technische Verbesserungen

### PDF-Export Robustheit
- **Fallback-Mechanismus**: Bei WeasyPrint-Fehlern wird HTML-Ansicht angezeigt
- **Optionale Abhängigkeiten**: System läuft auch ohne PDF-Export
- **Error-Handling**: Graceful Degradation bei Bibliotheksproblemen

### Automatische Tests
- **Selenium-Integration**: Vollständige End-to-End-Tests
- **Automatischer Start**: Tests laufen nach jedem Serverstart
- **Detaillierte Berichte**: Erfolg/Fehler mit Zeitstempel

### Sicherheit
- **Mandantenfähigkeit**: Company-basierte Datenisolation
- **Sichere Uploads**: Validierung von Dateitypen und -größen
- **CSRF-Schutz**: Vollständige CSRF-Absicherung
- **Session-Management**: Sichere Cookie-Konfiguration

---

## Hinweise zu Passwort-Reset-Texten
Die Standard-Templates von Django werden verwendet. Eigene Texte/Designs können durch Anlegen eigener Templates in `templates/registration/` oder `templates/accounts/` angepasst werden (z.B. `password_reset_email.html`, `password_reset_form.html`).

---

## Hinweise zu 2FA und Rate-Limit
- **2FA**: Für Zwei-Faktor-Authentifizierung kann z.B. [django-two-factor-auth](https://github.com/Bouke/django-two-factor-auth) integriert werden.
- **Rate-Limit/Brute-Force-Schutz**: Empfohlen wird [django-axes](https://django-axes.readthedocs.io/) oder [django-ratelimit](https://github.com/jsocol/django-ratelimit) für Login-Versuche.
- Diese Features sind vorbereitet, aber nicht aktiviert. Siehe Code-Kommentare und Hinweise in der README.

---

## 🚀 Nächste Verbesserungen

### Geplante Features:
1. **Erweiterte PDF-Funktionalität**
   - Digitale Unterschriften
   - Wasserzeichen und Branding
   - Batch-PDF-Export

2. **Mobile App**
   - React Native / Flutter
   - Offline-Funktionalität
   - Push-Benachrichtigungen

3. **Erweiterte Analytics**
   - Dashboard-Metriken
   - Performance-Tracking
   - Benutzer-Verhalten

4. **API-Erweiterungen**
   - REST-API für externe Integrationen
   - Webhook-System
   - Third-Party-Integrationen

### Technische Optimierungen:
1. **Performance**
   - Redis-Caching
   - Datenbank-Optimierung
   - CDN-Integration

2. **Sicherheit**
   - 2FA-Integration
   - Rate-Limiting
   - Audit-Logs

3. **Deployment**
   - Docker-Container
   - CI/CD-Pipeline
   - Auto-Scaling

---

## Logging, Error-Tracking & Monitoring

### Logging
- Alle sicherheitsrelevanten und wichtigen Ereignisse werden in der Datei `django-security.log` gespeichert (siehe LOGGING in `pv_protocol/settings.py`).
- Fehler und Warnungen werden zusätzlich in der Konsole ausgegeben.

### Error-Tracking (Optional)
- **Sentry**: Für detailliertes Error-Tracking (DSN in .env konfigurieren)
- **Prometheus**: Für Performance-Monitoring und Metriken
- **Custom Logging**: Für spezifische Anwendungslogik

### Monitoring
- **Health Checks**: Automatische Systemüberwachung
- **Performance-Metriken**: Datenbank, API, Frontend-Performance
- **Benutzer-Aktivität**: Login-Patterns, Feature-Nutzung

---

## Support & Wartung

### Regelmäßige Wartung
- **Datenbank-Backups**: Automatische Backups (empfohlen)
- **Security-Updates**: Regelmäßige Dependency-Updates
- **Performance-Monitoring**: Kontinuierliche Überwachung

### Troubleshooting
- **Logs prüfen**: `django-security.log` für Fehler
- **Tests ausführen**: `python selenium_test.py` für E2E-Tests
- **Datenbank prüfen**: `python manage.py check` für System-Integrität

---

## Lizenz & Kontakt

Dieses Projekt ist für den internen Gebrauch konzipiert. Bei Fragen oder Problemen siehe die Dokumentation oder kontaktieren Sie das Entwicklungsteam. 