from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from installations.models import Customer, PVInstallation, InstallationImage
from protocols.models import ProtocolTemplate, Protocol, ProtocolFile, Task
from payments.models import SubscriptionPlan, Subscription, Payment

class SicherheitsTests(TestCase):
    """
    Grundlegende Sicherheitstests für das PV-Protokoll-System.
    Testet User-Registrierung, Login, Rechte, Datei-Upload und Passwort-Validierung.
    """
    def setUp(self):
        # Lege einen Admin und einen Techniker an
        self.admin = User.objects.create_user(username='admin', password='AdminPass123!', role='admin', email='admin@example.com', is_superuser=True, is_staff=True)
        self.technician = User.objects.create_user(username='tech', password='TechPass123!', role='technician', email='tech@example.com')
        self.client = Client()

    def test_login(self):
        """Testet erfolgreichen Login und Logout"""
        login = self.client.login(username='admin', password='AdminPass123!')
        self.assertTrue(login)
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_passwort_validierung(self):
        """Testet, dass schwache Passwörter abgelehnt werden"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'weakuser',
            'email': 'weak@example.com',
            'first_name': 'Weak',
            'last_name': 'User',
            'role': 'technician',
            'password1': '123',
            'password2': '123',
        })
        self.assertContains(response, 'Dieses Passwort ist zu kurz', status_code=200)

    def test_dateiupload_installationimage(self):
        """Testet den Upload eines gültigen und eines ungültigen Bildes"""
        self.client.login(username='admin', password='AdminPass123!')
        customer = Customer.objects.create(user=self.admin)
        installation = PVInstallation.objects.create(
            operator=customer,
            name='Bildtest',
            installation_number='ANL000002',
            total_power_kw=5.0,
            number_of_modules=10,
            address='Teststraße 2',
            created_by=self.admin
        )
        # Gültiges Bild
        image = SimpleUploadedFile('bild.jpg', b'filecontent', content_type='image/jpeg')
        img = InstallationImage(installation=installation, image=image, uploaded_by=self.admin)
        try:
            img.full_clean()
        except Exception as e:
            self.fail(f'Gültiger Bild-Upload schlug fehl: {e}')
        # Ungültiger Dateityp
        bad_image = SimpleUploadedFile('bild.exe', b'filecontent', content_type='application/octet-stream')
        img_bad = InstallationImage(installation=installation, image=bad_image, uploaded_by=self.admin)
        with self.assertRaises(Exception):
            img_bad.full_clean()

    def test_rechteverwaltung(self):
        """Testet, dass Techniker keinen Zugriff auf Admin-Seiten haben"""
        self.client.login(username='tech', password='TechPass123!')
        response = self.client.get('/admin/')
        self.assertNotEqual(response.status_code, 200)

    def test_protocolfile_upload(self):
        """Testet den Upload einer erlaubten und einer nicht erlaubten Protokolldatei"""
        self.client.login(username='admin', password='AdminPass123!')
        customer = Customer.objects.create(user=self.admin)
        installation = PVInstallation.objects.create(
            operator=customer,
            name='Protokolltest',
            installation_number='ANL000003',
            total_power_kw=7.5,
            number_of_modules=20,
            address='Teststraße 3',
            created_by=self.admin
        )
        template = ProtocolTemplate.objects.create(
            name='Testvorlage',
            template_type='installation',
            content={},
            created_by=self.admin
        )
        protocol = Protocol.objects.create(
            title='Testprotokoll',
            installation=installation,
            template=template,
            content={},
            created_by=self.admin
        )
        # Gültige Datei
        file = SimpleUploadedFile('test.pdf', b'filecontent', content_type='application/pdf')
        pf = ProtocolFile(protocol=protocol, file=file, filename='test.pdf', file_type='pdf', file_size=100, uploaded_by=self.admin)
        try:
            pf.full_clean()
        except Exception as e:
            self.fail(f'Gültiger Datei-Upload schlug fehl: {e}')
        # Nicht erlaubter Dateityp
        bad_file = SimpleUploadedFile('test.exe', b'filecontent', content_type='application/octet-stream')
        pf_bad = ProtocolFile(protocol=protocol, file=bad_file, filename='test.exe', file_type='exe', file_size=100, uploaded_by=self.admin)
        with self.assertRaises(Exception):
            pf_bad.full_clean()

class DashboardTest(TestCase):
    """
    Testet, ob der Testuser sich einloggen und das neue Anlagen-Dashboard aufrufen kann.
    """
    def setUp(self):
        User.objects.create_user(username='testuser', password='testpass123', role='technician', email='testuser@example.com')
        self.client = Client()

    def test_dashboard_access(self):
        login = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login)
        response = self.client.get('/installations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anlagenverwaltung Dashboard')
        self.assertContains(response, 'Kunden')
        self.assertContains(response, 'Anlagen')
        self.assertContains(response, 'Mit Kunde')
        self.assertContains(response, 'Ohne Kunde')

class EndToEndDummyTest(TestCase):
    """
    End-to-End-Test: Testet Login, Dashboard, alle Dummy-Menü-Links und Logout für den Testuser.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', role='technician', email='testuser@example.com')
        self.client = Client()

    def test_full_navigation(self):
        # Login
        login = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login)

        # Dashboard (neu)
        response = self.client.get('/installations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anlagenverwaltung Dashboard')

        # Anlagen-Liste
        response = self.client.get('/installations/list/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anlagenverwaltung')

        # Kunden-Liste
        response = self.client.get('/installations/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kundenverwaltung')

        # Aufgaben-Liste (Dummy)
        response = self.client.get('/protocols/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo-Seite')

        # Protokoll-Liste (Dummy)
        response = self.client.get('/protocols/protocols/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo-Seite')

        # Vorlagen-Liste (Dummy)
        response = self.client.get('/protocols/templates/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo-Seite')

        # Logout
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.status_code, 302)

class KundenUndAnlagenViewsTest(TestCase):
    """
    Testet Listen- und Detailansichten für Kunden und Anlagen (inkl. Rechte, Suche, Templates).
    """
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='AdminPass123!', role='admin', email='admin@example.com', is_superuser=True, is_staff=True)
        self.kunde_user = User.objects.create_user(username='kunde', password='KundePass123!', role='customer', email='kunde@example.com', first_name='Klaus', last_name='Kunde')
        self.kunde = Customer.objects.create(user=self.kunde_user, customer_number='KUN000001')
        self.installation = PVInstallation.objects.create(
            name='Testanlage',
            location='Berlin',
            module_type='Mono',
            module_manufacturer='SolarMax',
            operator=self.kunde,
            size=10.5,
            total_power_kw=10.5,
            number_of_modules=30,
            address='Musterstraße 1, 10115 Berlin',
            created_by=self.admin
        )
        self.client = Client()

    def test_kundenliste_als_admin(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kundenverwaltung')
        self.assertContains(response, 'Klaus Kunde')
        self.assertTemplateUsed(response, 'installations/customer_list.html')

    def test_kundendetail_als_admin(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:customer_detail', args=[self.kunde.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kundendaten')
        self.assertContains(response, 'Klaus Kunde')
        self.assertTemplateUsed(response, 'installations/customer_detail.html')

    def test_kundendetail_als_fremder_user_verboten(self):
        fremder = User.objects.create_user(username='fremd', password='Fremd123!', role='customer', email='fremd@example.com')
        self.client.login(username='fremd', password='Fremd123!')
        response = self.client.get(reverse('installations:customer_detail', args=[self.kunde.pk]))
        self.assertEqual(response.status_code, 403)

    def test_kundendetail_als_eigener_user(self):
        self.client.login(username='kunde', password='KundePass123!')
        response = self.client.get(reverse('installations:customer_detail', args=[self.kunde.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Klaus Kunde')

    def test_kundenliste_suche(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:customer_list') + '?q=Klaus')
        self.assertContains(response, 'Klaus Kunde')
        response = self.client.get(reverse('installations:customer_list') + '?q=Unbekannt')
        self.assertContains(response, 'Keine Kunden gefunden')

    def test_anlagenliste_als_admin(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:installation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anlagenverwaltung')
        self.assertContains(response, 'Testanlage')
        self.assertTemplateUsed(response, 'installations/installation_list.html')

    def test_anlagendetail_als_admin(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:installation_detail', args=[self.installation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anlagendaten')
        self.assertContains(response, 'Testanlage')
        self.assertTemplateUsed(response, 'installations/installation_detail.html')

    def test_anlagendetail_als_fremder_user_verboten(self):
        fremder = User.objects.create_user(username='fremd', password='Fremd123!', role='customer', email='fremd@example.com')
        self.client.login(username='fremd', password='Fremd123!')
        response = self.client.get(reverse('installations:installation_detail', args=[self.installation.pk]))
        self.assertEqual(response.status_code, 403)

    def test_anlagendetail_als_berechtigter_kunde(self):
        self.client.login(username='kunde', password='KundePass123!')
        response = self.client.get(reverse('installations:installation_detail', args=[self.installation.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testanlage')

    def test_anlagenliste_suche(self):
        self.client.login(username='admin', password='AdminPass123!')
        response = self.client.get(reverse('installations:installation_list') + '?q=Berlin')
        self.assertContains(response, 'Testanlage')
        response = self.client.get(reverse('installations:installation_list') + '?q=Unbekannt')
        self.assertContains(response, 'Keine Anlagen gefunden') 