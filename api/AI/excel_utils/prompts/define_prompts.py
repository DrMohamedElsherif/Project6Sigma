DEFINE_PROMPTS = {
"D-VoC to CTx": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende CSV-Daten und extrahiere alle Voice-of-Customer-Informationen.

    Für jede Kundenstimme/Zeile extrahiere:
    - defineVoc3: Intern (1) oder Extern (2)? Bei Unsicherheit: 0
    - defineVoc4: Kostenaspekt betroffen? (true/false)
    - defineVoc5: Qualitätsaspekt betroffen? (true/false)
    - defineVoc6: Zeitaspekt betroffen? (true/false)
    - defineVoc7: Die Originalaussage der Kundenstimme
    - defineVoc8: Wer hat das gesagt?
    - defineVoc9: Woher kommt die Aussage? NICHT BUCHSTÄBLICH EXCEL ZEILE SONDERN PROJEKTNAME
    - defineVoc10: Kernthema/Stichworte
    - defineVoc11: CTx/Parameter/Spezifikation

    WICHTIG:
    - defineVoc2 MUSS immer ein Array sein
    - Jede Zeile = ein Objekt im Array
    - Wenn Daten fehlen, verwende: "" für Text, false für Booleans, 0 für defineVoc3
    - Antworte NUR mit JSON, kein Markdown

    CSV-Daten:
    {data}

    Gib aus:
    {{"defineVoc2": [...]}}""",
"D-SIPOC": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgendes SIPOC-CSV und extrahiere alle Informationen.

    Die Tabelle hat folgende Spalten:
    1. LIEFERANTEN (Suppliers)
    2. EINGABEN (Inputs)
    3. PROZESS (Process) > Startereigniss, Prozessschritte/Aktivitäten, Endergebnis
    4. AUSGABEN (Outputs)
    5. KUNDEN (Customers)

    Beachte dabei:
    1. Identifiziere den Prozessstart und das Prozessende
    2. Erfasse alle Prozessschritte/Aktivitäten als ARRAY
    3. Identifiziere alle Outputs und zugehörige Kunden als ARRAYS
    4. Identifiziere alle Inputs und zugehörige Lieferanten als ARRAYS
    5. Erfasse alle Kennzahlen (KPIs) mit ihren Werten und Einheiten als ARRAY
    6. Extrahiere eine kurze Prozessbeschreibung oder einen Kommentar

    KRITISCH WICHTIG ZUR DATENSTRUKTUR:
    - defineSipoc8, defineSipoc12, defineSipoc19 und defineSipoc26 MÜSSEN immer Arrays sein
    - Diese Arrays müssen mindestens ein Element enthalten, auch wenn nur ein Eintrag erkennbar ist
    - Jedes Array-Element muss exakt die vorgegebene Struktur haben
    - WICHTIG: Lasse Inputs und Outputs VOLLSTÄNDIG WEG, wenn sie leer/nicht vorhanden sind. Füge keine leeren Einträge ein!

    Gib deine Antwort AUSSCHLIESSLICH in folgendem JSON-Format zurück:

    {
    "defineSipoc": {
        "defineSipoc6": "Startpunkt/Startereignis des Prozesses",
        "defineSipoc8": [
        { "defineSipoc9": "Prozessschritt 1" },
        { "defineSipoc9": "Prozessschritt 2" }
        ],
        "defineSipoc10": "Endpunkt/Endereignis des Prozesses",
        "defineSipoc12": [
        {
            "defineSipoc14": "Output 1",
            "defineSipoc16": [
            { "defineSipoc17": "Kunde für Output 1" }
            ]
        },
        {
            "defineSipoc14": "Output 2",
            "defineSipoc16": [
            { "defineSipoc17": "Kunde 1 für Output 2" },
            { "defineSipoc17": "Kunde 2 für Output 2" }
            ]
        }
        ],
        "defineSipoc19": [
        {
            "defineSipoc21": "Input 1",
            "defineSipoc23": [
            { "defineSipoc24": "Lieferant für Input 1" }
            ]
        },
        {
            "defineSipoc21": "Input 2",
            "defineSipoc23": [
            { "defineSipoc24": "Lieferant 1 für Input 2" },
            { "defineSipoc24": "Lieferant 2 für Input 2" }
            ]
        }
        ],
        "defineSipoc26": [
        {
            "defineSipoc28": "KPI/Messgröße 1",
            "defineSipoc30": "Wert/Einheit 1"
        },
        {
            "defineSipoc28": "KPI/Messgröße 2",
            "defineSipoc30": "Wert/Einheit 2"
        }
        ],
        "defineSipoc31": "Zusammenfassender Kommentar zum Prozess"
    }
    }

    Beispiele für korrekte Array-Strukturen:

    1. Für einen einzelnen Prozessschritt:
    "defineSipoc8": [
        { "defineSipoc9": "Ein Prozessschritt" }
    ]

    2. Für einen einzelnen Output mit einem Kunden:
    "defineSipoc12": [
        {
        "defineSipoc14": "Ein Output",
        "defineSipoc16": [
            { "defineSipoc17": "Ein Kunde" }
        ]
        }
    ]

    WICHTIG:
    - Stelle sicher, dass ALLE Felder im JSON ausgefüllt sind.
    - Wenn Informationen fehlen, verwende einen leeren String ("") oder leere Arrays ([]).
    - Ordne die Informationen korrekt den jeweiligen Schlüsseln zu.
    - Antworte AUSSCHLIESSLICH mit dem JSON-Objekt ohne zusätzlichen Text oder Markdown.
    - Die Felder defineSipoc8, defineSipoc12, defineSipoc19, defineSipoc26 MÜSSEN Arrays sein.

    CSV-Daten:
    {data}""",
"Info-Sammlung": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Informationen, Fakten und Hypothesen.

    Für jede Information/Zeile extrahiere:
    - defineFacts6: Die Information/Beschreibung des Sachverhalts
    - defineFacts7: Ist es ein Fakt ("fact") oder eine Hypothese ("hypothesis")?
    - defineFacts9: Bezieht sich auf die Vergangenheit? (true/false)
    - defineFacts10: Bezieht sich auf die Gegenwart? (true/false)
    - defineFacts11: Bezieht sich auf die Zukunft? (true/false)
    - defineFacts12: Ansprechpartner (Kontaktperson)
    - defineFacts13: Kommentar (optional)

    Zusätzlich extrahiere:
    - defineFacts2: Das Datum im Format YYYY-MM-DD

    WICHTIG:
    - defineFacts4 MUSS immer ein Array sein
    - Jede Zeile = ein Objekt im Array
    - defineFacts7 MUSS entweder "fact" oder "hypothesis" sein
    - defineFacts9, defineFacts10, defineFacts11 MÜSSEN Booleans sein
    - defineFacts2 MUSS im ISO-Format YYYY-MM-DD sein
    - Wenn Daten fehlen, verwende: "" für Text, false für Booleans
    - Antworte NUR mit JSON, kein Markdown

    Excel-Daten:
    {data}

    Gib aus:
    {{"defineFacts2": "YYYY-MM-DD", "defineFacts4": [...], "defineFacts13": ""}}""",
"D-Problembeschreibung": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Informationen zur Problembeschreibung nach der 8D-Methode (Ist-Zustand).

    Die Tabelle hat typischerweise folgende Struktur mit Fragen:
    1. "An welchem Produkt / Prozess tritt das Problem auf?"
    2. "Wo genau tritt das Problem auf?"
    3. "Seit wann tritt das Problem auf?"

    Extrahiere folgende Felder:
    - defineProblem1: Allgemeine Problembeschreibung
    - defineProblem2: Betroffene Produkte/Produktfamilien (aus Frage 1)
    - defineProblem3: Nicht betroffene Produkte/Produktfamilien (aus Frage 1)
    - defineProblem4: Gemeinsamkeiten/Unterschiede zwischen betroffenen Produkten (aus Frage 1)
    - defineProblem5: Genaue Lage des Problems innerhalb des Produkts (aus Frage 2)
    - defineProblem6: Ähnliche Orte im Produkt, die NICHT betroffen sind (aus Frage 2)
    - defineProblem7: Gemeinsamkeiten/Unterschiede der räumlichen Lage (aus Frage 2)
    - defineProblem8: Zeitpunkt, an dem das Problem erstmals auftrat (aus Frage 3)
    - defineProblem9: Zeitpunkte, an denen das Problem NICHT auftrat (aus Frage 3)
    - defineProblem10: Besondere Ereignisse (Änderungen in Abläufen, neue Maschinen, neue Lieferanten, etc.) (aus Frage 3)
    - defineProblem11: Fehlerverlauf - MUSS einer dieser Werte sein: "konstant", "zyklisch", "stetig fallend", "zufällig", "sporadisch"
    - defineProblem12: Einordnung des Fehlerverlaufs basierend auf Fehleraufschreibungen und Daten

    WICHTIG:
    - Alle Felder sind Textfelder
    - defineProblem11 MUSS exakt einem der vordefinierten Werte entsprechen
    - Wenn Informationen nicht vorhanden sind, verwende einen leeren String ("")
    - Antworte NUR mit JSON, kein Markdown

    Excel-Daten:
    {data}

    Gib aus:
    {{"defineProblem": {{...}}}}""",
"D-Status": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Statusinformationen zum Projektfortschritt.

    Die Tabelle hat typischerweise folgende 5 Sektionen mit je 3 Feldern:

    1. KOSTEN (Cost)
    - defineStatus1: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus2: Zusammenfassung/Beschreibung
    - defineStatus3: Risiko (risk, onPlan, offPlan, notEvaluated)
    - defineStatus4: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus3 = "risk" oder "offPlan"
    - defineStatus5: Kommentar

    2. QUALITÄT (Quality)
    - defineStatus12: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus13: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus12 = "risk" oder "offPlan"
    - defineStatus14: Kommentar

    3. ZEIT (Time)
    - defineStatus21: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus22: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus21 = "risk" oder "offPlan"
    - defineStatus23: Kommentar

    4. UMFANG (Scope)
    - defineStatus31: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus32: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus31 = "risk" oder "offPlan"
    - defineStatus33: Kommentar

    5. PROZESSRISIKO / INTERAKTION (Process Risk/Interaction)
    - defineStatus41: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus42: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus41 = "risk" oder "offPlan"
    - defineStatus43: Kommentar

    6. SONSTIGES (Miscellaneous)
    - defineStatus51: Status (onPlan, offPlan, risk, notEvaluated)
    - defineStatus52: Abweichung korrigierbar? (yes/no) - NUR wenn defineStatus51 = "risk" oder "offPlan"
    - defineStatus53: Kommentar

    WICHTIG:
    - Status-Felder MÜSSEN exakt einen dieser Werte haben: "onPlan", "offPlan", "risk", "notEvaluated"
    - Korrigierbar-Felder (defineStatus4, 13, 22, 32, 42, 52) sind OPTIONAL und LEER, wenn der entsprechende Status nicht "risk" oder "offPlan" ist
    - Korrigierbar-Felder können NUR "yes" oder "no" sein, oder leer
    - Kommentar-Felder sind optional und können leer sein
    - Wenn Informationen fehlen, verwende einen leeren String ("")
    - Antworte NUR mit JSON, kein Markdown

    Excel-Daten:
    {data}

    Gib aus:
    {{"defineStatus1": "...", "defineStatus2": "...", ..., "defineStatus53": ""}}""",
"D-Review Protokoll": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Informationen aus dem Review-Protokoll.

    Die Tabelle hat typischerweise folgende Struktur:
    - Projektname, Projektnummer, Projektphase, Projektleiter und Datum befinden sich in den oberen Zeilen
    - "2. Inhalte" - Darunter folgt eine oder mehrere Zeilen mit dem Inhalt/den besprochenen Themen
    - "3. Beschlüsse" - Darunter folgen Beschlüsse (optional)
    - "4. Sonstiges" - Darunter folgen Sonstiges/Besonderheiten
    - "Weiter im Projekt*:" zeigt an, ob das Projekt fortgesetzt wird (Ja/Nein)
    - "Begründung (falls nein):" enthält den Grund, falls nicht fortgesetzt

    Extrahiere folgende Felder:
    - defineReviewProtocol3: Projektphase/Phasenname (aus "Projektphase:" Feld)
    - defineReviewProtocol4: Teilnehmer (aus "Projektleiter" oder falls vorhanden Teilnehmerliste - kommagetrennt)
    - defineReviewProtocol5: Datum des Reviews (ISO-Format YYYY-MM-DD, aus "Datum:" Feld)
    - defineReviewProtocol6: Startzeit (HH:MM Format) - falls vorhanden, sonst ""
    - defineReviewProtocol7: Endzeit (HH:MM Format) - falls vorhanden, sonst ""
    - defineReviewProtocol11: Inhalte/Zusammenfassung (Text UNTER "2. Inhalte")
    - defineReviewProtocol20: Sonstiges/Besonderheiten (Text UNTER "4. Sonstiges")
    - defineReviewProtocol22: Projekt fortsetzen? (true = Ja, false = Nein, basierend auf "Weiter im Projekt*:")
    - defineReviewProtocol24: Grund für Nichtfortführung (Text aus "Begründung (falls nein):" - nur wenn defineReviewProtocol22 = false)

    WICHTIG:
    - defineReviewProtocol5 MUSS im ISO-Format YYYY-MM-DD sein
    - defineReviewProtocol6 und defineReviewProtocol7 MÜSSEN im HH:MM Format sein (oder "")
    - defineReviewProtocol22 MUSS ein Boolean sein (true oder false)
    - defineReviewProtocol4 sollte Namen mit Kommas und Leerzeichen trennen
    - Extrahiere Text UNTER den Sektions-Überschriften (2. Inhalte, 4. Sonstiges), nicht die Überschriften selbst
    - Wenn Daten fehlen, verwende: "" für Text-Felder, false für defineReviewProtocol22
    - Antworte NUR mit JSON, kein Markdown

    Excel-Daten:
    {data}

    Gib aus:
    {{"defineReviewProtocol3": "...", "defineReviewProtocol4": "...", "defineReviewProtocol5": "YYYY-MM-DD", "defineReviewProtocol6": "HH:MM", "defineReviewProtocol7": "HH:MM", "defineReviewProtocol11": "...", "defineReviewProtocol20": "...", "defineReviewProtocol22": true/false, "defineReviewProtocol24": ""}}""",
"D-Stakeholderanalysis": """Du bist ein Datenextraktions-Spezialist. Analysiere die folgende Excel-Tabelle und extrahiere alle Stakeholder-Informationen zur Stakeholder-Analyse.

    Für jeden Stakeholder/jede Zeile extrahiere folgende Felder im Array defineSteakholder4:
    - defineSteakholder6: Name des Stakeholders
    - defineSteakholder7: Abteilung/Department
    - defineSteakholder8: Funktion/Rolle
    - defineSteakholder9: Organisationszugehörigkeit (z.B. "Internal", "External", "Customer", "Supplier")
    - defineSteakholder10: Sonstige Informationen/Anmerkungen (Textarea)
    - defineSteakholder12: Betroffenheit - MUSS einer sein von: 1 (hoch), 2 (mittel), 3 (gering)
    - defineSteakholder13: Einstellung zum Projekt - MUSS einer sein von: 1 (hoch), 2 (mittel), 3 (gering)
    - defineSteakholder14: Einstellung zum Projektleiter - MUSS einer sein von: 1 (hoch), 2 (mittel), 3 (gering)
    - defineSteakholder15: Einfluss auf Projekt - MUSS einer sein von: 1 (hoch), 2 (mittel), 3 (gering)
    - defineSteakholder16: Einfluss auf Projektleiter - MUSS einer sein von: 1 (hoch), 2 (mittel), 3 (gering)
    - defineSteakholder18: Maßnahmen (nested Array von Objekten mit):
      - defineSteakholder19: Beschreibung der Maßnahme
      - defineSteakholder20: Wer unterstützt die Maßnahme?
      - defineSteakholder21: Maßnahmencharakter - MUSS einer sein von: 1 (proaktiv), 2 (reaktiv)
      - defineSteakholder22: Maßnahmenkategorie - MUSS einer sein von: 1 (positives stärken), 2 (negatives abwenden)

    WICHTIG:
    - defineSteakholder4 MUSS immer ein Array sein (Top-Level Repeater)
    - Jede Zeile mit Stakeholder-Daten = ein Objekt im Array
    - Extrahiere NUR Zeilen, die einen Namen (defineSteakholder6) haben
    - Wenn KEINE Stakeholder in der Tabelle vorhanden sind, gib ein LEERES Array zurück
    - defineSteakholder18 (Measures) MUSS auch ein Array sein für jeden Stakeholder
    - Alle Select-Felder (defineSteakholder12-16, 21, 22) MÜSSEN numerische Werte sein (1, 2 oder 3)
    - KEINE 0-Werte verwenden - nur 1, 2, 3
    - Wenn Maßnahmen nicht vorhanden sind, kann defineSteakholder18 ein leeres Array sein
    - Wenn Daten fehlen, verwende: "" für Text-Felder, 3 als Default für Level-Felder (gering)
    - Antworte NUR mit JSON, kein Markdown

    Excel-Daten:
    {data}

    Gib aus:
    {{"defineSteakholder4": [...]}}""",
}

