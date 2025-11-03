ANALYSIS_PROMPTS = {
"A-Status": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Analyse-Status-Informationen zum Projektfortschritt.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "analysisStatus": {
        "analysisStatus79": "onPlan",
        "analysisStatus80": "Summary text here",
        "analysisStatus78_1": true,
        "analysisStatus83": "risk",
        "analysisStatus84": "yes",
        "analysisStatus85": "Cost comment text",
        "analysisStatus88": "onPlan",
        "analysisStatus89": "no",
        "analysisStatus90": "Quality comment text",
        "analysisStatus93": "offPlan",
        "analysisStatus94": "yes",
        "analysisStatus95": "Time comment text",
        "analysisStatus98": "notEvaluated",
        "analysisStatus99": "",
        "analysisStatus100": "Scope comment text",
        "analysisStatus103": "onPlan",
        "analysisStatus104": "no",
        "analysisStatus105": "Process risk comment text",
        "analysisStatus108": "risk",
        "analysisStatus109": "yes",
        "analysisStatus110": "Miscellaneous comment text"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    
    OVERALL PROJECT STATUS:
    - analysisStatus79: Stand des Gesamtprojektes (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus80: Zusammenfassung (textarea)
    - analysisStatus78_1: Maßnahmen aus vorheriger Phase überprüft (boolean)
    
    COST:
    - analysisStatus83: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus84: Korrigierbar (yes, no) - NUR wenn analysisStatus83 = risk oder offPlan
    - analysisStatus85: Kommentar (textarea)
    
    QUALITY:
    - analysisStatus88: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus89: Korrigierbar (yes, no) - NUR wenn analysisStatus88 = risk oder offPlan
    - analysisStatus90: Kommentar (textarea)
    
    TIME:
    - analysisStatus93: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus94: Korrigierbar (yes, no) - NUR wenn analysisStatus93 = risk oder offPlan
    - analysisStatus95: Kommentar (textarea)
    
    SCOPE:
    - analysisStatus98: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus99: Korrigierbar (yes, no) - NUR wenn analysisStatus98 = risk oder offPlan
    - analysisStatus100: Kommentar (textarea)
    
    PROCESS RISK / INTERACTION:
    - analysisStatus103: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus104: Korrigierbar (yes, no) - NUR wenn analysisStatus103 = risk oder offPlan
    - analysisStatus105: Kommentar (textarea)
    
    MISCELLANEOUS:
    - analysisStatus108: Status (notEvaluated, onPlan, risk, offPlan)
    - analysisStatus109: Korrigierbar (yes, no) - NUR wenn analysisStatus108 = risk oder offPlan
    - analysisStatus110: Kommentar (textarea)

    ANWEISUNGEN:
    1. Extrahiere den Gesamtprojektstatus und Zusammenfassung
    2. Für jede Kategorie (Cost, Quality, Time, Scope, Process Risk, Miscellaneous) extrahiere: Status, Korrigierbarkeit und Kommentar
    3. Für fehlende Werte: "" für Text-Felder, false für Booleans, "notEvaluated" für Status-Felder
    4. Status-Felder müssen exakt einer dieser Werte sein: notEvaluated, onPlan, risk, offPlan
    5. Korrigierbar-Felder müssen exakt "yes" oder "no" sein
    6. Korrigierbar-Felder sind CONDITIONAL - nur ausfüllen wenn Status = risk oder offPlan, sonst ""
    7. analysisStatus78_1 ist ein Boolean (true/false)

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"A-Review Protokoll": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Review-Protokoll-Informationen für die Analyse-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "analysisReviewProtocol": {
        "analysisReviewProtocol3": "Projektphase",
        "analysisReviewProtocol4": "teilnehmer",
        "analysisReviewProtocol5": "YYYY-MM-DD",
        "analysisReviewProtocol6": "HH:mm",
        "analysisReviewProtocol7": "HH:mm",
        "analysisReviewProtocol25": true,
        "analysisReviewProtocol11": "Inhalte text",
        "analysisReviewProtocol20": "sonstiges text",
        "analysisReviewProtocol22": true,
        "analysisReviewProtocol24": "Begründung text"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - analysisReviewProtocol3: Projektphase (text)
    - analysisReviewProtocol4: Teilnehmer (text)
    - analysisReviewProtocol5: Datum (Format: YYYY-MM-DD)
    - analysisReviewProtocol6: Uhrzeit Start (Format: HH:mm, 24-Stunden-Format)
    - analysisReviewProtocol7: Uhrzeit End (Format: HH:mm, 24-Stunden-Format)
    - analysisReviewProtocol25: Maßnahmen aus vorheriger Phase überprüft (boolean)
    - analysisReviewProtocol11: Inhalte (textarea)
    - analysisReviewProtocol20: Sonstiges (textarea)
    - analysisReviewProtocol22: Weiter im Projekt? Slider/Toggle (boolean)
    - analysisReviewProtocol24: Begründung (textarea)

    ANWEISUNGEN:
    1. Extrahiere die Projektphase und Teilnehmer als Text
    2. Datum muss im Format YYYY-MM-DD sein
    3. Uhrzeiten müssen im 24-Stunden-Format HH:mm sein (z.B. 09:00, 17:30)
    4. Für fehlende Werte: "" für Text-Felder, false für Booleans
    5. analysisReviewProtocol25 und analysisReviewProtocol22 sind Booleans (true/false)
    6. Alle Text-Felder dürfen Zeilenumbrüche enthalten

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
}