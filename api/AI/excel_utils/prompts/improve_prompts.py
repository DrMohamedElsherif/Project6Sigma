IMPROVE_PROMPTS = {
    "I-Status": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Status-Informationen zum Projektfortschritt in der Improve-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "improveStatus": {
        "improveReview62": "onPlan",
        "improveReview63": "Summary text about the overall project status",
        "improveReview63_1": true,
        "improveReview66": "onPlan",
        "improveReview67": "yes",
        "improveReview68": "Comment about costs perspective",
        "improveReview71": "risk",
        "improveReview72": "no",
        "improveReview73": "Comment about quality perspective",
        "improveReview76": "onPlan",
        "improveReview77": "yes",
        "improveReview78": "Comment about time perspective",
        "improveReview81": "offPlan",
        "improveReview82": "yes",
        "improveReview83": "Comment about scope perspective",
        "improveReview86": "notEvaluated",
        "improveReview87": "no",
        "improveReview88": "Comment about process risk / interaction",
        "improveReview91": "onPlan",
        "improveReview92": "yes",
        "improveReview93": "Comment about miscellaneous"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    
    OVERALL PROJECT STATUS:
    - improveReview62: Stand des Gesamtprojektes (notEvaluated, onPlan, risk, offPlan)
    - improveReview63: Zusammenfassung (textarea)
    - improveReview63_1: Maßnahmen aus vorheriger Phase überprüft (boolean)
    
    KOSTEN:
    - improveReview66: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview67: Korrigierbar (yes, no) - NUR wenn improveReview66 = risk oder offPlan
    - improveReview68: Kommentar (textarea)
    
    QUALITÄT:
    - improveReview71: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview72: Korrigierbar (yes, no) - NUR wenn improveReview71 = risk oder offPlan
    - improveReview73: Kommentar (textarea)
    
    ZEIT:
    - improveReview76: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview77: Korrigierbar (yes, no) - NUR wenn improveReview76 = risk oder offPlan
    - improveReview78: Kommentar (textarea)
    
    SCOPE:
    - improveReview81: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview82: Korrigierbar (yes, no) - NUR wenn improveReview81 = risk oder offPlan
    - improveReview83: Kommentar (textarea)
    
    PROZESSRISIKO/WECHSELWIRKUNG:
    - improveReview86: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview87: Korrigierbar (yes, no) - NUR wenn improveReview86 = risk oder offPlan
    - improveReview88: Kommentar (textarea)
    
    SONSTIGES:
    - improveReview91: Status (notEvaluated, onPlan, risk, offPlan)
    - improveReview92: Korrigierbar (yes, no) - NUR wenn improveReview91 = risk oder offPlan
    - improveReview93: Kommentar (textarea)

    ANWEISUNGEN:
    1. Extrahiere den Gesamtprojektstatus und Zusammenfassung
    2. Für jede Kategorie (Kosten, Qualität, Zeit, Scope, Prozessrisiko, Sonstiges) extrahiere: Status, Korrigierbarkeit und Kommentar
    3. Für fehlende Werte: "" für Text-Felder, false für Booleans, "notEvaluated" für Status-Felder
    4. Status-Felder müssen exakt einer dieser Werte sein: notEvaluated, onPlan, risk, offPlan
    5. Korrigierbar-Felder müssen exakt "yes" oder "no" sein
    6. Korrigierbar-Felder sind CONDITIONAL - nur ausfüllen wenn Status = risk oder offPlan, sonst ""
    7. improveReview63_1 ist ein Boolean (true/false)

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"I-Review Protokoll": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Review-Protokoll-Informationen für die Improve-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "improveReviewProtocol": {
        "improveReviewProtocol3": "Project phase name",
        "improveReviewProtocol4": "Participant names",
        "improveReviewProtocol5": "2025-10-23",
        "improveReviewProtocol6": "09:00",
        "improveReviewProtocol7": "10:30",
        "improveReviewProtocol25": true,
        "improveReviewProtocol11": "Content and discussion points from the review",
        "improveReviewProtocol20": "Miscellaneous notes",
        "improveReviewProtocol22": true,
        "improveReviewProtocol24": "Reasoning for continuing or not continuing the project"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - improveReviewProtocol3: Projektphase (text)
    - improveReviewProtocol4: Teilnehmer (text)
    - improveReviewProtocol5: Datum (Format: YYYY-MM-DD)
    - improveReviewProtocol6: Uhrzeit Start (Format: HH:mm, 24-Stunden-Format)
    - improveReviewProtocol7: Uhrzeit End (Format: HH:mm, 24-Stunden-Format)
    - improveReviewProtocol25: Maßnahmen aus vorheriger Phase überprüft (boolean)
    - improveReviewProtocol11: Inhalte (textarea)
    - improveReviewProtocol20: Sonstiges (textarea)
    - improveReviewProtocol22: Weiter im Projekt? Slider/Toggle (boolean)
    - improveReviewProtocol24: Begründung (textarea)

    ANWEISUNGEN:
    1. Extrahiere die Projektphase und Teilnehmer als Text
    2. Datum muss im Format YYYY-MM-DD sein
    3. Uhrzeiten müssen im 24-Stunden-Format HH:mm sein (z.B. 09:00, 17:30)
    4. Für fehlende Werte: "" für Text-Felder, false für Booleans
    5. improveReviewProtocol25 und improveReviewProtocol22 sind Booleans (true/false)
    6. Alle Text-Felder dürfen Zeilenumbrüche enthalten

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"I-Ideenliste": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Ideen aus der Ideenliste der Improve-Phase.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "improveBrainstorming": {
        "improveBrainstorming1": [
          {
            "improveBrainstorming2": "Idea text description",
            "improveBrainstorming3": "followedUp",
            "improveBrainstorming6": "Comment when followedUp is selected"
          },
          {
            "improveBrainstorming2": "Another idea",
            "improveBrainstorming3": "discarded",
            "improveBrainstorming6": ""
          }
        ]
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - improveBrainstorming1: Array of ideas (repeater)
    - improveBrainstorming2: Idee (text field)
    - improveBrainstorming3: Bewertung (select field with values: notEvaluated, discarded, followedUp)
    - improveBrainstorming6: Kommentar (textarea, nur wenn improveBerainstorming3 = "followedUp")

    ANWEISUNGEN:
    1. Extrahiere jede Idee als separates Objekt in der improveBrainstorming1 Array
    2. Für jede Idee extrahiere: Text, Bewertungsstatus und optional einen Kommentar
    3. improveBrainstorming3 muss exakt einer dieser Werte sein: notEvaluated, discarded, followedUp
    4. improveBrainstorming6 (Kommentar) ist CONDITIONAL - nur ausfüllen wenn improveBrainstorming3 = "followedUp", sonst ""
    5. Für fehlende Werte: "" für Text-Felder, "notEvaluated" für Status-Felder
    6. Die Array kann mehrere Ideen enthalten

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
}