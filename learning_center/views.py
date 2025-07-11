from django.shortcuts import render
from django.views import View

# Beispielhafte Struktur für Lektionen (kann später in die DB ausgelagert werden)
LEKTIONEN = [
    {
        'slug': 'grundlagen-pv-wartung',
        'titel': 'Grundlagen der PV-Anlagen-Wartung',
        'beschreibung': 'Einführung in die Wartung von Photovoltaik-Anlagen, Sicherheitsaspekte und typische Wartungsaufgaben.',
        'inhalt': '''
            <h3>Was ist Wartung bei PV-Anlagen?</h3>
            <ul>
                <li>Regelmäßige Sichtkontrolle der Module, Verkabelung und Unterkonstruktion</li>
                <li>Überprüfung der Wechselrichter und Sicherungen</li>
                <li>Reinigung der Module (bei Bedarf)</li>
                <li>Dokumentation aller Wartungsarbeiten</li>
            </ul>
            <p>Siehe auch: <a href="https://www.solarpowereurope.org/insights/thematic-reports/operation-and-maintenance-best-practice-guidelines-version-6-0" target="_blank">O&M Best Practice Guidelines (SolarPower Europe)</a></p>
        '''
    },
    {
        'slug': 'praxiswissen-grosse-pv-anlagen',
        'titel': 'Praxiswissen: Wartung großer PV-Anlagen',
        'beschreibung': 'Planung, Durchführung und Dokumentation der Wartung bei großen PV-Dachanlagen.','inhalt': '''
            <h3>Typische Wartungsaufgaben</h3>
            <ul>
                <li>Visuelle Inspektion der Module und Unterkonstruktion</li>
                <li>Thermografie zur Erkennung von Hotspots</li>
                <li>Überprüfung der elektrischen Anschlüsse (DC/AC)</li>
                <li>Testen der Schutz- und Sicherheitseinrichtungen</li>
                <li>Reinigung und Pflege der Anlage</li>
            </ul>
            <p>Vertiefung: <a href="https://www.vdi-wissensforum.de/weiterbildung-bau/praxiswissen-grosse-pv/" target="_blank">VDI Wissensforum: Praxiswissen Große PV-Anlagen</a></p>
        '''
    },
    {
        'slug': 'emp-nfpa-70b',
        'titel': 'Wartungsprogramme nach NFPA 70B','beschreibung': 'Strukturierte Wartungsprogramme für PV- und Batteriesysteme nach dem internationalen Standard NFPA 70B.','inhalt': '''
            <h3>Wartungsprogramm (EMP) nach NFPA 70B</h3>
            <ul>
                <li>Personalqualifikation und Sicherheit</li>
                <li>Wartungsintervalle nach Anlagenzustand</li>
                <li>Dokumentation und Prüfprotokolle</li>
                <li>Typische Prüfungen: Isolationsmessung, Thermografie, Sichtkontrolle</li>
            </ul>
            <p>Mehr dazu: <a href="https://www.heatspring.com/courses/nfpa-70b-a-new-standard-for-electrical-equipment-maintenance" target="_blank">HeatSpring: NFPA 70B Kurs</a></p>
        '''
    },
    {
        'slug': 'pv-wartung-praxis',
        'titel': 'Wartung in der Praxis: Checklisten & Tipps','beschreibung': 'Checklisten, häufige Fehlerquellen und Tipps für die tägliche Wartung.','inhalt': '''
            <h3>Checkliste für die Wartung</h3>
            <ul>
                <li>Module auf Verschmutzung, Schäden und Hotspots prüfen</li>
                <li>Wechselrichter-Status und Fehlerprotokolle kontrollieren</li>
                <li>Schutzschalter und Sicherungen testen</li>
                <li>Ertragsdaten regelmäßig auswerten</li>
            </ul>
            <p>Weitere Infos: <a href="https://www.milkthesun.com/en/photovoltaic-operations-maintenance-guide" target="_blank">MilkTheSun: O&M Guide</a></p>
        '''
    },
    {
        'slug': 'video-seminare',
        'titel': 'Video-Seminare & Online-Kurse','beschreibung': 'Empfohlene Video-Seminare und Online-Kurse zur PV-Wartung.','inhalt': '''
            <ul>
                <li><a href="https://www.bingen.de/stadt/stadtwerke/klimaschutz/photovoltaik/online-seminarreihe-solar-1" target="_blank">Online-Seminarreihe Solar 2025 (Stadt Bingen)</a></li>
                <li><a href="https://www.youtube.com/results?search_query=pv+wartung+schulung" target="_blank">YouTube: PV Wartung Schulung</a></li>
            </ul>
        '''
    }
]

class LearningCenterView(View):
    def get(self, request):
        return render(request, 'learning_center/learning_center.html', {'lektionen': LEKTIONEN})

class LearningLessonView(View):
    def get(self, request, slug):
        lektion = next((l for l in LEKTIONEN if l['slug'] == slug), None)
        if not lektion:
            from django.http import Http404
            raise Http404('Lektion nicht gefunden')
        return render(request, 'learning_center/lesson_detail.html', {'lektion': lektion}) 