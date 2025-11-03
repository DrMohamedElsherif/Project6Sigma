MEASURE_PROMPTS = {
"M-Prozesserfassung": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende CSV-Daten und extrahiere alle Prozessinformationen nach der 5W1H-Methode.

    Für jeden Prozessschritt/jede Zeile extrahiere:
    - measureProcessCapture6: Prozessschritt-Name oder Bezeichnung
    - measureProcessCapture7: WER (Prozessverantwortlicher/Owner/Rolle)
    - measureProcessCapture8: WAS (Beschreibung des Ablaufs)
    - measureProcessCapture9: WIE (Beschreibung der Umsetzung)
    - measureProcessCapture10: WO (Ort der Durchführung)
    - measureProcessCapture11: WANN (Zeitpunkt/Häufigkeit/Dauer)
    - measureProcessCapture12: WARUM (Grund/Zweck)

    WICHTIG:
    - measureProcessCapture5 MUSS immer ein Array sein
    - Jede Zeile = ein Objekt im Array
    - Wenn Daten fehlen, verwende: "" für alle Text-Felder
    - Behalte die Tabellenstruktur und Spaltenzuordnung konsequent bei
    - Antworte NUR mit JSON, kein Markdown

    CSV-Daten:
    {data}

    Gib aus:
    {{"measureProcessCapture5": [...]}}""",
"M-Prozessparametermodell": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Prozessparameter nach dem Prozessparametermodell (Y = f(X, Z)).

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben - KEINE zusätzlichen Klammern oder Felder:

    {
      "measurePpModel": {
        "measurePpModelY": [
          {
            "measurePpModelY1": "Wert",
            "measurePpModelY1Value": "Einheit",
            "measurePpModelY2": "Wert",
            "measurePpModelY2Value": "Einheit",
            "measurePpModelY3": "",
            "measurePpModelY3Value": "",
            "measurePpModelY4": "",
            "measurePpModelY4Value": "",
            "measurePpModelY5": "",
            "measurePpModelY5Value": "",
            "measurePpModelY6": "",
            "measurePpModelY6Value": "",
            "measurePpModelY7": "",
            "measurePpModelY7Value": "",
            "measurePpModelY8": "",
            "measurePpModelY8Value": "",
            "measurePpModelY9": "",
            "measurePpModelY9Value": ""
          }
        ],
        "measurePpModelX": [
          {"measurePpModelXItem": "Temperatur", "measurePpModelXItemValue": "°C"},
          {"measurePpModelXItem": "Druck", "measurePpModelXItemValue": "bar"}
        ],
        "measurePpModelZ": [
          {"measurePpModelZItem": "Luftfeuchtigkeit", "measurePpModelZItemValue": "%"}
        ]
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - measurePpModelY1, measurePpModelY1Value, measurePpModelY2, measurePpModelY2Value, ..., measurePpModelY9, measurePpModelY9Value
    - measurePpModelXItem, measurePpModelXItemValue (für Input-Objekte)
    - measurePpModelZItem, measurePpModelZItemValue (für Disturbance-Objekte)

    ANWEISUNGEN:
    1. Analysiere die OUTPUT (Y) Spalte: Extrahiere bis zu 9 Parameter mit Namen und Einheiten
    2. Analysiere die INPUT (X) Spalte: Extrahiere alle Steuerparameter mit Namen und Einheiten
    3. Analysiere die DISTURBANCE (Z) Spalte: Extrahiere alle Störgrößen mit Namen und Einheiten
    4. Wenn ein Parameter nicht vorhanden ist, verwende "" (leerer String) für Wert und Einheit
    5. Wenn INPUT oder DISTURBANCE nicht vorhanden sind, gib leere Arrays zurück []

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE zusätzlichen Klammern oder Braces
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"M-Datenerfassungsplan": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Datenerfassungsplaneinträge.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "measureDataCollectionPlan": {
        "measureDataCollectionPlan3": [
          {
            "measureDataCollectionPlan5": "Messgröße",
            "measureDataCollectionPlan6": "Einheit",
            "measureDataCollectionPlan7": "controlVariable|interferenceVariable|resultVariable",
            "measureDataCollectionPlan8": "continuous|attributiv",
            "measureDataCollectionPlan9": "präzise definition",
            "measureDataCollectionPlan13": "Präzise beschreibung",
            "measureDataCollectionPlan14": "durchführender",
            "measureDataCollectionPlan15": "YYYY-MM-DD",
            "measureDataCollectionPlan16": "Basis/Rahmenbedingung/Stichprobenkonzept",
            "measureDataCollectionPlan19": "Quelle/ort",
            "measureDataCollectionPlan20": true,
            "measureDataCollectionPlan21": false,
            "measureDataCollectionPlan22": false,
            "measureDataCollectionPlan23": false,
            "measureDataCollectionPlan25": "lower bound",
            "measureDataCollectionPlan26": "upper bound"
          }
        ]
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - measureDataCollectionPlan3: Array für mehrere Einträge
    - measureDataCollectionPlan5: Messgröße (text)
    - measureDataCollectionPlan6: Einheit (text)
    - measureDataCollectionPlan7: Art der Messgröße (controlVariable, interferenceVariable, resultVariable)
    - measureDataCollectionPlan8: Art der daten (continuous, attributiv)
    - measureDataCollectionPlan9: Präzise definition (text)
    - measureDataCollectionPlan13: Präzise beschreibung (textarea)
    - measureDataCollectionPlan14: Durchführender (text)
    - measureDataCollectionPlan15: Datum (Format: YYYY-MM-DD)
    - measureDataCollectionPlan16: Basis/Rahmenbedingung/Stichprobenkonzept (text)
    - measureDataCollectionPlan19: Quelle/ort (text)
    - measureDataCollectionPlan20-23: Haupttyp Checkboxes (boolean)
    - measureDataCollectionPlan25: Lower Bound (text, nur wenn field7 = controlVariable oder interferenceVariable)
    - measureDataCollectionPlan26: Upper Bound (text, nur wenn field7 = controlVariable oder interferenceVariable)

    ANWEISUNGEN:
    1. Extrahiere jeden Dateneintrag als separates Objekt im Array
    2. Für fehlende Werte: "" für Text-Felder, false für Booleans
    3. Datum muss im Format YYYY-MM-DD sein
    4. Kontrollgrenzen (25, 26) nur ausfüllen wenn field7 = controlVariable oder interferenceVariable
    5. Genau eine Checkbox (20-23) sollte true sein

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - Die Antwort muss mit { beginnen und mit } enden
    - BENUTZE KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}

    Excel-Daten:
    {data}""",
"M-Status": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Statusinformationen zum Projektfortschritt.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "measureStatus": {
        "measureStatus1": "onPlan",
        "measureStatus2": "Summary text here",
        "measureStatus3": true,
        "measureStatus4": "onPlan",
        "measureStatus5": "yes",
        "measureStatus6": "Cost comment text",
        "measureStatus14": "onPlan",
        "measureStatus15": "no",
        "measureStatus16": "Quality comment text",
        "measureStatus24": "risk",
        "measureStatus25": "yes",
        "measureStatus26": "Time comment text",
        "measureStatus34": "offPlan",
        "measureStatus35": "no",
        "measureStatus36": "Scope comment text",
        "measureStatus44": "notEvaluated",
        "measureStatus45": "",
        "measureStatus46": "Process risk comment text",
        "measureStatus54": "onPlan",
        "measureStatus55": "yes",
        "measureStatus56": "Miscellaneous comment text"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - measureStatus1: Stand des Gesamtprojektes (notEvaluated, onPlan, risk, offPlan)
    - measureStatus2: Zusammenfassung (textarea)
    - measureStatus3: Maßnahmen aus vorheriger Phase überprüft (boolean)
    
    KOSTEN:
    - measureStatus4: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus5: Korrigierbar (yes, no)
    - measureStatus6: Kommentar (textarea)
    
    QUALITÄT:
    - measureStatus14: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus15: Korrigierbar (yes, no)
    - measureStatus16: Kommentar (textarea)
    
    ZEIT:
    - measureStatus24: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus25: Korrigierbar (yes, no)
    - measureStatus26: Kommentar (textarea)
    
    SCOPE:
    - measureStatus34: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus35: Korrigierbar (yes, no)
    - measureStatus36: Kommentar (textarea)
    
    PROZESSRISIKO/WECHSELWIRKUNG:
    - measureStatus44: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus45: Korrigierbar (yes, no)
    - measureStatus46: Kommentar (textarea)
    
    SONSTIGES:
    - measureStatus54: Status (notEvaluated, onPlan, risk, offPlan)
    - measureStatus55: Korrigierbar (yes, no)
    - measureStatus56: Kommentar (textarea)

    ANWEISUNGEN:
    1. Extrahiere den Gesamtprojektstatus und Zusammenfassung
    2. Für jede Kategorie (Kosten, Qualität, Zeit, Scope, Prozessrisiko, Sonstiges) extrahiere: Status, Korrigierbarkeit und Kommentar
    3. Für fehlende Werte: "" für Text-Felder, false für Booleans, "notEvaluated" für Status-Felder
    4. Status-Felder müssen exakt einer dieser Werte sein: notEvaluated, onPlan, risk, offPlan
    5. Korrigierbar-Felder müssen exakt "yes" oder "no" sein
    6. measureStatus3 ist ein Boolean (true/false)

    WICHTIG:
    - Antworte NUR mit dem JSON-Objekt
    - KEINE zusätzlichen Erklärungen vor oder nach dem JSON
    - KEINE Markdown-Formatierung
    - KEINE DOPPELTEN GESCHWUNGENEN KLAMMERN {{ oder }}
    - Die Antwort muss mit { beginnen und mit } enden

    Excel-Daten:
    {data}""",
"M-Review Protokoll": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Review-Protokoll-Informationen.

    STRUKTUR-ANFORDERUNG (SEHR WICHTIG):
    Die Antwort MUSS exakt folgende JSON-Struktur haben:

    {
      "measureReviewProtocol": {
        "measureReviewProtocol3": "Projektphase",
        "measureReviewProtocol4": "teilnehmer",
        "measureReviewProtocol5": "YYYY-MM-DD",
        "measureReviewProtocol6": "HH:mm",
        "measureReviewProtocol7": "HH:mm",
        "measureReviewProtocol25": true,
        "measureReviewProtocol11": "Inhalte text",
        "measureReviewProtocol20": "sonstiges text",
        "measureReviewProtocol22": true,
        "measureReviewProtocol24": "Begründung text"
      }
    }

    FELDNAMENKONVENTION - EXAKT SO SCHREIBEN:
    - measureReviewProtocol3: Projektphase (text)
    - measureReviewProtocol4: Teilnehmer (text)
    - measureReviewProtocol5: Datum (Format: YYYY-MM-DD)
    - measureReviewProtocol6: Uhrzeit Start (Format: HH:mm, 24-Stunden-Format)
    - measureReviewProtocol7: Uhrzeit End (Format: HH:mm, 24-Stunden-Format)
    - measureReviewProtocol25: Maßnahmen aus vorheriger Phase überprüft (boolean)
    - measureReviewProtocol11: Inhalte (textarea)
    - measureReviewProtocol20: Sonstiges (textarea)
    - measureReviewProtocol22: Weiter im Projekt? Slider/Toggle (boolean)
    - measureReviewProtocol24: Begründung (textarea)

    ANWEISUNGEN:
    1. Extrahiere die Projektphase und Teilnehmer als Text
    2. Datum muss im Format YYYY-MM-DD sein
    3. Uhrzeiten müssen im 24-Stunden-Format HH:mm sein (z.B. 09:00, 17:30)
    4. Für fehlende Werte: "" für Text-Felder, false für Booleans
    5. measureReviewProtocol25 und measureReviewProtocol22 sind Booleans (true/false)
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