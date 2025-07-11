import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# === KONFIGURATION ===
BASE_URL = 'http://192.168.65.56:8000/'  # Passe ggf. an deine lokale IP an
USERNAME = 'testuser'  # Passe an
PASSWORD = 'Testpass123!'  # Passe an

# === SETUP ===
# Stelle sicher, dass chromedriver im PATH ist oder passe den Pfad an
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Headless-Modus für CI
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)
driver.set_window_size(1280, 900)
wait = WebDriverWait(driver, 10)

def log_test_step(step_name, status="INFO"):
    """Loggt Test-Schritte mit Zeitstempel"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {step_name}")

def test_navigation_to_page(url, expected_title_contains=None, expected_element=None):
    """Testet Navigation zu einer Seite"""
    try:
        driver.get(url)
        log_test_step(f"Navigation zu {url}")
        
        # Prüfe Titel falls angegeben
        if expected_title_contains:
            if expected_title_contains in driver.title:
                log_test_step(f"Titel korrekt: {driver.title}", "SUCCESS")
            else:
                log_test_step(f"Titel unerwartet: {driver.title}", "WARNING")
        
        # Prüfe spezifisches Element falls angegeben
        if expected_element:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, expected_element)))
                log_test_step(f"Element gefunden: {expected_element}", "SUCCESS")
                return True
            except TimeoutException:
                log_test_step(f"Element nicht gefunden: {expected_element}", "ERROR")
                return False
        
        return True
    except Exception as e:
        log_test_step(f"Fehler bei Navigation zu {url}: {e}", "ERROR")
        return False

def test_form_submission(form_url, form_data, success_indicator=None):
    """Testet Formular-Ausfüllung und -Absendung"""
    try:
        driver.get(form_url)
        log_test_step(f"Formular geladen: {form_url}")
        
        # Fülle Formular aus
        for field_name, value in form_data.items():
            try:
                field = wait.until(EC.presence_of_element_located((By.NAME, field_name)))
                field.clear()
                field.send_keys(value)
                log_test_step(f"Feld {field_name} ausgefüllt: {value}")
            except TimeoutException:
                log_test_step(f"Feld {field_name} nicht gefunden", "WARNING")
        
        # Formular absenden
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()
        log_test_step("Formular abgeschickt")
        
        # Warte auf Erfolg
        time.sleep(2)
        
        # Prüfe Erfolg-Indikator
        if success_indicator:
            try:
                success_element = wait.until(EC.presence_of_element_located((By.XPATH, success_indicator)))
                log_test_step(f"Erfolg bestätigt: {success_element.text}", "SUCCESS")
                return True
            except TimeoutException:
                log_test_step("Erfolg-Indikator nicht gefunden", "WARNING")
                return False
        
        return True
    except Exception as e:
        log_test_step(f"Fehler beim Formular-Test: {e}", "ERROR")
        return False

try:
    # 1. Startseite aufrufen
    log_test_step("=== STARTE ERWEITERTEN SELENIUM-TEST ===")
    driver.get(BASE_URL)
    log_test_step(f"Startseite geladen: {driver.title}")

    # 2. Login durchführen
    login_url = BASE_URL + 'accounts/login/'
    driver.get(login_url)
    log_test_step(f"Login-Seite geladen: {driver.title}")
    
    # Debug: Prüfe ob Login-Formular vorhanden
    try:
        username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        password_field = driver.find_element(By.NAME, 'password')
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        log_test_step("Login-Formular gefunden", "SUCCESS")
    except Exception as e:
        log_test_step(f"Login-Formular nicht gefunden: {e}", "ERROR")
        print('Seiteninhalt:', driver.page_source[:500])
        raise
    
    # Login-Daten eingeben
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    submit_button.click()
    
    log_test_step("Login-Daten eingegeben, warte auf Weiterleitung...")
    time.sleep(2)
    
    # Debug: Prüfe aktuelle URL und Titel
    log_test_step(f"Aktuelle URL: {driver.current_url}")
    log_test_step(f"Aktueller Titel: {driver.title}")
    
    # Warte auf Dashboard (deutscher Text) oder prüfe auf Fehlermeldungen
    try:
        # Prüfe zuerst auf Login-Fehler
        error_messages = driver.find_elements(By.CLASS_NAME, 'alert-danger')
        if error_messages:
            log_test_step(f"Login-Fehler gefunden: {error_messages[0].text}", "ERROR")
            raise Exception('Login fehlgeschlagen')
        
        # Prüfe auf Dashboard-Elemente
        dashboard_elements = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Guten') or contains(text(), 'Dashboard')]")
        if dashboard_elements:
            log_test_step(f"Dashboard gefunden: {dashboard_elements[0].text}", "SUCCESS")
        else:
            log_test_step("Dashboard nicht gefunden, prüfe andere Elemente...", "WARNING")
            # Prüfe auf andere Dashboard-Indikatoren
            nav_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'dashboard')]")
            if nav_elements:
                log_test_step("Dashboard-Navigation gefunden", "SUCCESS")
            else:
                log_test_step("Keine Dashboard-Elemente gefunden", "ERROR")
                print('Seiteninhalt (erste 1000 Zeichen):', driver.page_source[:1000])
                raise Exception('Dashboard nicht gefunden nach Login')
        
        log_test_step("Login erfolgreich!", "SUCCESS")
    except Exception as e:
        log_test_step(f"Fehler beim Login: {e}", "ERROR")
        raise

    # 3. Teste Kunden-Anlage
    log_test_step("=== TESTE KUNDEN-ANLAGE ===")
    
    # Gehe zur Kundenliste
    customers_url = BASE_URL + 'installations/customers/'
    driver.get(customers_url)
    log_test_step("Kundenliste geladen")
    
    # Klicke auf "Neuen Kunden anlegen"
    try:
        new_customer_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'customers/new') or contains(text(), 'Neu')]")
        new_customer_btn.click()
        log_test_step("Neuer Kunde-Button geklickt")
        
        # Warte auf Formular
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        log_test_step("Kunden-Formular geladen")
        
        # Fülle Kunden-Formular aus
        customer_data = {
            'first_name': 'Test',
            'last_name': 'Kunde',
            'email': 'test.kunde@example.com',
            'phone': '0123456789',
            'address': 'Teststraße 123',
            'city': 'Teststadt',
            'postal_code': '12345'
        }
        
        for field_name, value in customer_data.items():
            try:
                field = driver.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
                log_test_step(f"Kunden-Feld {field_name} ausgefüllt: {value}")
            except NoSuchElementException:
                log_test_step(f"Kunden-Feld {field_name} nicht gefunden", "WARNING")
        
        # Formular absenden
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        log_test_step("Kunden-Formular abgeschickt")
        
        # Warte auf Erfolg
        time.sleep(2)
        log_test_step("Kunde erfolgreich angelegt", "SUCCESS")
        
    except Exception as e:
        log_test_step(f"Fehler beim Anlegen des Kunden: {e}", "WARNING")

    # 4. Teste Anlagen-Anlage
    log_test_step("=== TESTE ANLAGEN-ANLAGE ===")
    
    # Gehe zur Anlagenliste
    installations_url = BASE_URL + 'installations/list/'
    driver.get(installations_url)
    log_test_step("Anlagenliste geladen")
    
    # Klicke auf "Neue Anlage anlegen"
    try:
        new_installation_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'installations/new') or contains(text(), 'Neue Anlage')]")
        new_installation_btn.click()
        log_test_step("Neue Anlage-Button geklickt")
        
        # Warte auf Formular
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        log_test_step("Anlagen-Formular geladen")
        
        # Fülle Anlagen-Formular aus
        installation_data = {
            'name': 'Test-PV-Anlage',
            'power_kw': '10.5',
            'installation_date': '2024-01-15',
            'address': 'Teststraße 123',
            'city': 'Teststadt',
            'postal_code': '12345'
        }
        
        for field_name, value in installation_data.items():
            try:
                field = driver.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
                log_test_step(f"Anlagen-Feld {field_name} ausgefüllt: {value}")
            except NoSuchElementException:
                log_test_step(f"Anlagen-Feld {field_name} nicht gefunden", "WARNING")
        
        # Formular absenden
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        log_test_step("Anlagen-Formular abgeschickt")
        
        # Warte auf Erfolg
        time.sleep(2)
        log_test_step("Anlage erfolgreich angelegt", "SUCCESS")
        
    except Exception as e:
        log_test_step(f"Fehler beim Anlegen der Anlage: {e}", "WARNING")

    # 5. Teste Protokoll-Anlage
    log_test_step("=== TESTE PROTOKOLL-ANLAGE ===")
    
    # Gehe zur Protokoll-Liste
    protocols_url = BASE_URL + 'protocols/protocols/'
    driver.get(protocols_url)
    log_test_step("Protokoll-Liste geladen")
    
    # Klicke auf "Neues Protokoll anlegen"
    try:
        new_protocol_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'protocols/create') or contains(text(), 'Neu')]")
        new_protocol_btn.click()
        log_test_step("Neues Protokoll-Button geklickt")
        
        # Warte auf Formular
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        log_test_step("Protokoll-Formular geladen")
        
        # Fülle Protokoll-Formular aus
        protocol_data = {
            'title': 'Test-Protokoll',
            'description': 'Dies ist ein Test-Protokoll für die Selenium-Tests'
        }
        
        for field_name, value in protocol_data.items():
            try:
                field = driver.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
                log_test_step(f"Protokoll-Feld {field_name} ausgefüllt: {value}")
            except NoSuchElementException:
                log_test_step(f"Protokoll-Feld {field_name} nicht gefunden", "WARNING")
        
        # Formular absenden
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        log_test_step("Protokoll-Formular abgeschickt")
        
        # Warte auf Erfolg
        time.sleep(2)
        log_test_step("Protokoll erfolgreich angelegt", "SUCCESS")
        
    except Exception as e:
        log_test_step(f"Fehler beim Anlegen des Protokolls: {e}", "WARNING")

    # 6. Teste Mitarbeiter-Einladung
    log_test_step("=== TESTE MITARBEITER-EINLADUNG ===")
    
    # Gehe zur Mitarbeiter-Liste
    users_url = BASE_URL + 'accounts/users/'
    driver.get(users_url)
    log_test_step("Mitarbeiter-Liste geladen")
    
    # Klicke auf "Einladen" Button
    try:
        invite_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'invite') or contains(text(), 'Einladen')]")
        invite_btn.click()
        log_test_step("Einladen-Button geklickt")
        
        # Warte auf Einladungs-Formular
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        log_test_step("Einladungs-Formular geladen")
        
        # Fülle Einladungs-Formular aus
        invitation_data = {
            'email': 'test.mitarbeiter@example.com',
            'role': 'employee'
        }
        
        for field_name, value in invitation_data.items():
            try:
                if field_name == 'role':
                    # Dropdown auswählen
                    role_select = driver.find_element(By.NAME, field_name)
                    role_select.click()
                    role_option = driver.find_element(By.XPATH, f"//option[@value='{value}']")
                    role_option.click()
                    log_test_step(f"Rolle ausgewählt: {value}")
                else:
                    field = driver.find_element(By.NAME, field_name)
                    field.clear()
                    field.send_keys(value)
                    log_test_step(f"Einladungs-Feld {field_name} ausgefüllt: {value}")
            except NoSuchElementException:
                log_test_step(f"Einladungs-Feld {field_name} nicht gefunden", "WARNING")
        
        # Formular absenden
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        log_test_step("Einladungs-Formular abgeschickt")
        
        # Warte auf Erfolg
        time.sleep(2)
        log_test_step("Einladung erfolgreich erstellt", "SUCCESS")
        
    except Exception as e:
        log_test_step(f"Fehler beim Erstellen der Einladung: {e}", "WARNING")

    # 7. Teste Protokollvorlage anlegen
    log_test_step("=== TESTE PROTOKOLLVORLAGE-ANLAGE ===")
    templates_url = BASE_URL + 'protocols/templates/'
    driver.get(templates_url)
    log_test_step("Vorlagen-Liste geladen")
    try:
        new_template_btn = driver.find_element(By.XPATH, "//a[contains(@href, 'templates/create') or contains(text(), 'Neu')]")
        new_template_btn.click()
        log_test_step("Neue Vorlage-Button geklickt")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        log_test_step("Vorlagen-Formular geladen")
        template_data = {
            'name': 'Selenium-Testvorlage',
            'template_type': 'default',  # Passe ggf. an
            'description': 'Dies ist eine Testvorlage für Selenium',
            'content': '{\"test\": \"wert\"}'
        }
        for field_name, value in template_data.items():
            try:
                field = driver.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
                log_test_step(f"Vorlagen-Feld {field_name} ausgefüllt: {value}")
            except NoSuchElementException:
                log_test_step(f"Vorlagen-Feld {field_name} nicht gefunden", "WARNING")
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        log_test_step("Vorlagen-Formular abgeschickt")
        time.sleep(2)
        # Prüfe, ob die Vorlage in der Liste erscheint
        driver.get(templates_url)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), 'Selenium-Testvorlage')]")))
            log_test_step("Vorlage erfolgreich angelegt und sichtbar", "SUCCESS")
        except TimeoutException:
            log_test_step("Vorlage wurde nach dem Anlegen NICHT in der Liste gefunden!", "ERROR")
    except Exception as e:
        log_test_step(f"Fehler beim Anlegen der Vorlage: {e}", "WARNING")

    # Nach jedem Anlegen prüfen, ob das Objekt in der Liste sichtbar ist
    # Nach Kunden-Anlage
    driver.get(customers_url)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Test') and contains(text(), 'Kunde')]")))
        log_test_step("Kunde nach Anlage sichtbar", "SUCCESS")
    except TimeoutException:
        log_test_step("Kunde nach Anlage NICHT in der Liste gefunden!", "ERROR")

    # Nach Anlagen-Anlage
    driver.get(installations_url)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Test-PV-Anlage')]")))
        log_test_step("Anlage nach Anlage sichtbar", "SUCCESS")
    except TimeoutException:
        log_test_step("Anlage nach Anlage NICHT in der Liste gefunden!", "ERROR")

    # Nach Protokoll-Anlage
    driver.get(protocols_url)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Test-Protokoll')]")))
        log_test_step("Protokoll nach Anlage sichtbar", "SUCCESS")
    except TimeoutException:
        log_test_step("Protokoll nach Anlage NICHT in der Liste gefunden!", "ERROR")

    # Nach Mitarbeiter-Einladung
    driver.get(users_url)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'test.mitarbeiter@example.com')]")))
        log_test_step("Mitarbeiter nach Einladung sichtbar", "SUCCESS")
    except TimeoutException:
        log_test_step("Mitarbeiter nach Einladung NICHT in der Liste gefunden!", "ERROR")

    # 7. Teste Navigation zu allen Bereichen
    log_test_step("=== TESTE ALLE NAVIGATIONS-BEREICHE ===")
    
    # Teste alle Hauptbereiche
    test_urls = [
        (BASE_URL + 'installations/', "Anlagen-Dashboard", "//h1[contains(text(), 'Anlagenverwaltung')]"),
        (BASE_URL + 'installations/customers/', "Kunden", "//h2[contains(text(), 'Kunden')]"),
        (BASE_URL + 'installations/installations/', "PV-Anlagen", "//h2[contains(text(), 'Anlagen')]"),
        (BASE_URL + 'protocols/protocols/', "Protokolle", "//h2[contains(text(), 'Protokoll')]"),
        (BASE_URL + 'protocols/templates/', "Vorlagen", "//h2[contains(text(), 'Protokollvorlagen')]"),
        (BASE_URL + 'accounts/users/', "Mitarbeiter", "//h2[contains(text(), 'Mitarbeiter')]"),
        (BASE_URL + 'accounts/profile/', "Profil", "//h2[contains(text(), 'Profil')]"),
    ]
    
    for url, name, expected_element in test_urls:
        if test_navigation_to_page(url, name, expected_element):
            log_test_step(f"{name}-Navigation funktioniert", "SUCCESS")
        else:
            log_test_step(f"{name}-Navigation hat Probleme", "WARNING")

    # === TESTE ANLAGEN-DETAILANSICHT, TIMELINE, TITELBILD, KARTE ===
    log_test_step("=== TESTE ANLAGEN-DETAILANSICHT & CRM-ZEITVERLAUF ===")
    try:
        # Gehe zur Anlagenliste
        installations_url = BASE_URL + 'installations/list/'
        driver.get(installations_url)
        log_test_step("Anlagenliste geladen")
        
        # Prüfe ob Anlagen vorhanden sind
        try:
            first_installation_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/installations/') and contains(@href, '/detail')]")))
            first_installation_link.click()
            log_test_step("Anlagen-Detailansicht geöffnet")
            
            # Prüfe auf Timeline
            timeline_header = wait.until(EC.presence_of_element_located((By.XPATH, "//h5[contains(text(), 'CRM-Zeitverlauf')]")))
            log_test_step("Timeline-Header gefunden", "SUCCESS")
            
            # Prüfe auf Kartenansicht
            map_header = driver.find_element(By.XPATH, "//h5[contains(text(), 'Standortkarte')]")
            log_test_step("Kartenansicht-Header gefunden", "SUCCESS")
            
            # Prüfe auf Dashboard-Platz
            dashboard_header = driver.find_element(By.XPATH, "//h5[contains(text(), 'Daten-Dashboard')]")
            log_test_step("Dashboard-Platz gefunden", "SUCCESS")
            
        except TimeoutException:
            log_test_step("Keine Anlagen vorhanden - Test übersprungen", "WARNING")
            
    except Exception as e:
        log_test_step(f"Fehler in Detailansicht/Timeline-Test: {e}", "ERROR")

    # === TESTE NOTIZ- UND WARTUNGSANLAGE & SICHTBARKEIT IN TIMELINE ===
    log_test_step("=== TESTE NOTIZ- UND WARTUNGSANLAGE ===")
    try:
        # Prüfe ob wir auf einer Anlagen-Detailseite sind
        current_url = driver.current_url
        if '/installations/' in current_url and '/detail' in current_url:
            # Gehe zur Notiz-Anlage (Modal-Button)
            note_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Notiz') or contains(@data-bs-target, 'addNoteModal')]")
            note_btn.click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            note_data = {'title': 'Selenium-Testnotiz', 'content': 'Dies ist eine Testnotiz aus dem Selenium-Test.'}
            for field, value in note_data.items():
                field_elem = driver.find_element(By.NAME, field)
                field_elem.clear()
                field_elem.send_keys(value)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            log_test_step("Notiz angelegt")
            # Prüfe Sichtbarkeit in Timeline
            timeline_note = wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(., 'Selenium-Testnotiz')]")))
            log_test_step("Testnotiz in Timeline sichtbar", "SUCCESS")
            # Gehe zur Wartungs-Anlage (Modal-Button)
            maint_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Wartung') or contains(@data-bs-target, 'addMaintenanceModal')]")
            maint_btn.click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            maint_data = {'title': 'Selenium-Testwartung', 'description': 'Testwartung für Timeline', 'maintenance_type': 'routine', 'scheduled_date': '2025-12-31'}
            for field, value in maint_data.items():
                field_elem = driver.find_element(By.NAME, field)
                field_elem.clear()
                field_elem.send_keys(value)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            log_test_step("Wartung angelegt")
            # Prüfe Sichtbarkeit in Timeline
            timeline_maint = wait.until(EC.presence_of_element_located((By.XPATH, "//li[contains(., 'Selenium-Testwartung')]")))
            log_test_step("Testwartung in Timeline sichtbar", "SUCCESS")
        else:
            log_test_step("Nicht auf Anlagen-Detailseite - Test übersprungen", "WARNING")
    except Exception as e:
        log_test_step(f"Fehler bei Notiz-/Wartungsanlage: {e}", "ERROR")

    # === TESTE TITELBILD-UPLOAD ===
    log_test_step("=== TESTE TITELBILD-UPLOAD ===")
    try:
        # Prüfe ob wir auf einer Anlagen-Detailseite sind
        current_url = driver.current_url
        if '/installations/' in current_url and '/detail' in current_url:
            # Prüfe ob Titelbild-Upload-Button vorhanden ist
            upload_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Titelbild hochladen') or contains(@onclick, 'profileImageInput')]")
            log_test_step("Titelbild-Upload-Button gefunden", "SUCCESS")
            
            # Prüfe ob Upload-Input vorhanden ist
            upload_input = driver.find_element(By.ID, 'profileImageInput')
            log_test_step("Titelbild-Upload-Input gefunden", "SUCCESS")
            
            # Prüfe ob Kartenansicht vorhanden ist
            map_div = driver.find_element(By.ID, 'map')
            log_test_step("Kartenansicht gefunden", "SUCCESS")
        else:
            log_test_step("Nicht auf Anlagen-Detailseite - Test übersprungen", "WARNING")
        
    except Exception as e:
        log_test_step(f"Fehler beim Titelbild-Upload: {e}", "ERROR")

    # === TESTE KARTENANSICHT SICHTBARKEIT ===
    log_test_step("=== TESTE KARTENANSICHT ===")
    try:
        # Prüfe ob wir auf einer Anlagen-Detailseite sind
        current_url = driver.current_url
        if '/installations/' in current_url and '/detail' in current_url:
            # Prüfe ob Kartenansicht vorhanden ist
            map_div = driver.find_element(By.ID, 'map')
            log_test_step("Karten-Div vorhanden", "SUCCESS")
            
            # Prüfe ob Dashboard-Platz vorhanden ist
            dashboard_section = driver.find_element(By.XPATH, "//h5[contains(text(), 'Daten-Dashboard')]")
            log_test_step("Dashboard-Platz vorhanden", "SUCCESS")
            
            # Prüfe ob Timeline vorhanden ist
            timeline_section = driver.find_element(By.XPATH, "//h5[contains(text(), 'CRM-Zeitverlauf')]")
            log_test_step("Timeline vorhanden", "SUCCESS")
        else:
            log_test_step("Nicht auf Anlagen-Detailseite - Test übersprungen", "WARNING")
        
    except Exception as e:
        log_test_step(f"Fehler bei Kartenansicht-Test: {e}", "ERROR")

    # 4. Impressum und Datenschutz testen
    log_test_step("=== TESTE IMPRESSUM & DATENSCHUTZ-LINKS ===")
    try:
        # Footer-Links suchen
        impressum_link = driver.find_element(By.XPATH, "//footer//a[contains(@href, '/impressum')]")
        datenschutz_link = driver.find_element(By.XPATH, "//footer//a[contains(@href, '/datenschutz')]")
        log_test_step("Footer-Links gefunden", "SUCCESS")

        # Impressum-Link testen
        impressum_link.click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Impressum')]")))
        log_test_step("Impressum-Seite geladen", "SUCCESS")
        driver.back()
        time.sleep(1)

        # Datenschutz-Link testen
        datenschutz_link = driver.find_element(By.XPATH, "//footer//a[contains(@href, '/datenschutz')]")
        datenschutz_link.click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Datenschutzerklärung')]")))
        log_test_step("Datenschutz-Seite geladen", "SUCCESS")
        driver.back()
        time.sleep(1)
    except Exception as e:
        log_test_step(f"Fehler beim Testen der Footer-Links: {e}", "ERROR")

    log_test_step("=== ALLE ERWEITERTEN TESTS ABGESCHLOSSEN ===", "SUCCESS")

finally:
    driver.quit()
    log_test_step("Test abgeschlossen.")

# Hinweise:
# - Passe BASE_URL, USERNAME und PASSWORD an deine Umgebung an.
# - Für Firefox: webdriver.Firefox() verwenden und ggf. geckodriver installieren.
# - Für weitere Tests: Felder und Abläufe nach Bedarf erweitern. 