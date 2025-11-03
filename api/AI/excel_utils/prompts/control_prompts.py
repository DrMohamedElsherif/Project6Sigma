CONTROL_PROMPTS = {
"C-Review _ Lessons Learned": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Lessons-Learned-Einträge.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgendes JSON-Objekt haben:

    
    {
    "controlLessonsLearned1": [
        {
        "controlLessonsLearned2": "innerPerspektive|outerPerspektive",
        "controlLessonsLearned3": true,
        "controlLessonsLearned4": false,
        "controlLessonsLearned5": false,
        "controlLessonsLearned6": false,
        "controlLessonsLearned7": "Kommentar text",
        "controlLessonsLearned8": "Konkrete Ableitung / Handlungsempfehlung"
        }
    ]
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - controlLessonsLearned: äußeres Array (kann mehrere Objekte enthalten)
    - controlLessonsLearned1: Array mit repeater-Einträgen (mehrere Reihen)
    - controlLessonsLearned2: Perspektive (select: innerPerspektive oder outerPerspektive)
    - controlLessonsLearned3: Ablauf (boolean)
    - controlLessonsLearned4: Zielerreichung (boolean)
    - controlLessonsLearned5: Vorbereitung (boolean)
    - controlLessonsLearned6: Sonstiges (boolean)
    - controlLessonsLearned7: Kommentar (textarea/string)
    - controlLessonsLearned8: Konkrete Ableitung/Handlungsempfehlung (textarea/string)

    ANWEISUNGEN:
    1. Extrahiere jede Zeile des Repeaters als eigenes Objekt in controlLessonsLearned1.
    2. Für fehlende Textfelder: "" verwenden.
    3. Für fehlende Boolean-Felder: false verwenden.
    4. Bei ungültigem select-Wert für controlLessonsLearned2: setze "".
    5. Antworte NUR mit dem JSON-Objekt, keine Erklärungen, keine Markdown.
    6. Verwende KEINE doppelten geschwungenen Klammern {{ }}.

    Excel-Daten:
    {data}""",
"C-Status": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Status-Informationen zum Projektfortschritt in der Control-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "controlStatus": {
        "controlReview55": "onPlan",
        "controlReview56": "Summary text about the overall project status",
        "controlReview57": true,
        "controlReview60": "onPlan",
        "controlReview61": "yes",
        "controlReview62": "Comment about costs perspective",
        "controlReview65": "risk",
        "controlReview66": "no",
        "controlReview67": "Comment about quality perspective",
        "controlReview70": "onPlan",
        "controlReview71": "yes",
        "controlReview72": "Comment about time perspective",
        "controlReview75": "offPlan",
        "controlReview76": "yes",
        "controlReview77": "Comment about scope perspective",
        "controlReview80": "notEvaluated",
        "controlReview81": "no",
        "controlReview82": "Comment about process risk / interaction",
        "controlReview85": "onPlan",
        "controlReview86": "yes",
        "controlReview87": "Comment about miscellaneous"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    
    OVERALL PROJECT STATUS:
    - controlReview55: Stand des Gesamtprojektes (notEvaluated, onPlan, risk, offPlan)
    - controlReview56: Zusammenfassung (textarea)
    - controlReview57: Maßnahmen aus vorheriger Phase überprüft (boolean)
    
    KOSTEN:
    - controlReview60: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview61: Korrigierbar (yes, no) - NUR wenn controlReview60 = risk oder offPlan
    - controlReview62: Kommentar (textarea)
    
    QUALITÄT:
    - controlReview65: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview66: Korrigierbar (yes, no) - NUR wenn controlReview65 = risk oder offPlan
    - controlReview67: Kommentar (textarea)
    
    ZEIT:
    - controlReview70: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview71: Korrigierbar (yes, no) - NUR wenn controlReview70 = risk oder offPlan
    - controlReview72: Kommentar (textarea)
    
    SCOPE:
    - controlReview75: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview76: Korrigierbar (yes, no) - NUR wenn controlReview75 = risk oder offPlan
    - controlReview77: Kommentar (textarea)
    
    PROZESSRISIKO/WECHSELWIRKUNG:
    - controlReview80: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview81: Korrigierbar (yes, no) - NUR wenn controlReview80 = risk oder offPlan
    - controlReview82: Kommentar (textarea)
    
    SONSTIGES:
    - controlReview85: Status (notEvaluated, onPlan, risk, offPlan)
    - controlReview86: Korrigierbar (yes, no) - NUR wenn controlReview85 = risk oder offPlan
    - controlReview87: Kommentar (textarea)

    ANWEISUNGEN:
    1. Extrahiere den Gesamtprojektstatus und Zusammenfassung
    2. Für jede Kategorie (Kosten, Qualität, Zeit, Scope, Prozessrisiko, Sonstiges) extrahiere: Status, Korrigierbarkeit und Kommentar
    3. Für fehlende Werte: "" für Text-Felder, false für Booleans, "notEvaluated" für Status-Felder
    4. Status-Felder müssen exakt einer dieser Werte sein: notEvaluated, onPlan, risk, offPlan
    5. Korrigierbar-Felder müssen exakt "yes" oder "no" sein
    6. Korrigierbar-Felder sind CONDITIONAL - nur ausfüllen wenn Status = risk oder offPlan, sonst ""
    7. controlReview57 ist ein Boolean (true/false)

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"C-Review Protokoll": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Review-Protokoll-Informationen für die Control-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "controlReviewProtocol": {
        "controlReviewProtocol3": "Project phase name",
        "controlReviewProtocol4": "Participant names",
        "controlReviewProtocol5": "2025-10-23",
        "controlReviewProtocol6": "09:00",
        "controlReviewProtocol7": "10:30",
        "measureReviewProtocol25": true,
        "controlReviewProtocol11": "Content and discussion points from the review meeting",
        "controlReviewProtocol20": "Miscellaneous notes and observations",
        "controlReviewProtocol22": true,
        "controlReviewProtocol24": "Reasoning for continuing or not continuing the project"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - controlReviewProtocol3: Projektphase (text)
    - controlReviewProtocol4: Teilnehmer (text)
    - controlReviewProtocol5: Datum (Format: YYYY-MM-DD)
    - controlReviewProtocol6: Uhrzeit Start (Format: HH:mm, 24-Stunden-Format)
    - controlReviewProtocol7: Uhrzeit End (Format: HH:mm, 24-Stunden-Format)
    - measureReviewProtocol25: Maßnahmen aus vorheriger Phase überprüft (boolean)
    - controlReviewProtocol11: Inhalte (textarea)
    - controlReviewProtocol20: Sonstiges (textarea)
    - controlReviewProtocol22: Weiter im Projekt? Slider/Toggle (boolean)
    - controlReviewProtocol24: Begründung (textarea)

    ANWEISUNGEN:
    1. Extrahiere die Projektphase und Teilnehmer als Text
    2. Datum muss im Format YYYY-MM-DD sein
    3. Uhrzeiten müssen im 24-Stunden-Format HH:mm sein (z.B. 09:00, 17:30)
    4. Für fehlende Werte: "" für Text-Felder, false für Booleans
    5. measureReviewProtocol25 und controlReviewProtocol22 sind Booleans (true/false)
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