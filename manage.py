#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import time

def run_automated_tests():
    """Führt automatische Tests nach dem Serverstart durch"""
    print("\n" + "="*60)
    print("🚀 AUTOMATISCHE TESTS NACH SERVERSTART")
    print("="*60)
    
    # Warte kurz, bis Server vollständig gestartet ist
    time.sleep(3)
    
    try:
        # Führe Selenium-Test aus
        print("📋 Führe Selenium-Test aus...")
        result = subprocess.run([sys.executable, 'selenium_test.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Selenium-Test erfolgreich!")
            print("📊 Test-Ergebnisse:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Selenium-Test fehlgeschlagen!")
            print("📋 Fehlerdetails:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Selenium-Test abgebrochen (Timeout)")
    except FileNotFoundError:
        print("⚠️  Selenium-Test-Datei nicht gefunden")
    except Exception as e:
        print(f"❌ Fehler beim automatischen Test: {e}")
    
    print("="*60 + "\n")

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pv_protocol.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Prüfe ob runserver gestartet wird
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # Starte Tests in separatem Thread nach Serverstart
        import threading
        test_thread = threading.Thread(target=run_automated_tests, daemon=True)
        test_thread.start()
    
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
