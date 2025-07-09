## Possible prompt improvement for process_capture:

Analysiere das dargestellte Prozessdiagramm oder Dokument und extrahiere strukturierte Prozessinformationen.

Gib die Antwort als gültiges JSON-Objekt zurück mit folgendem Format:
{
  "measureProcessCapture5": [
    {
      "measureProcessCapture6": "Prozessschritt-Name",
      "measureProcessCapture7": "WER (Prozessverantwortlicher/Owner)",
      "measureProcessCapture8": "WAS (Beschreibung des Ablaufs)",
      "measureProcessCapture9": "WIE (Beschreibung der Umsetzung)",
      "measureProcessCapture10": "WO (Ort der Durchführung)",
      "measureProcessCapture11": "WANN (Zeitpunkt/Häufigkeit)",
      "measureProcessCapture12": "WARUM (Grund/Zweck)"
    }
  ]
}

KRITISCH WICHTIGE HINWEISE:

1. ZUORDNUNG DER FELDER (Dieses Schema entspricht der 5W1H-Methode):
   - measureProcessCapture6: "Prozessschritt" - Name oder Bezeichnung des Prozessschritts
   - measureProcessCapture7: "WER" - Person oder Rolle, die für diesen Schritt verantwortlich ist
   - measureProcessCapture8: "WAS" - Beschreibung des Ablaufs oder was getan wird
   - measureProcessCapture9: "WIE" - Beschreibung der Umsetzung oder wie es getan wird
   - measureProcessCapture10: "WO" - Ort oder Bereich, wo der Schritt stattfindet
   - measureProcessCapture11: "WANN" - Zeitpunkt, Dauer oder Häufigkeit des Schritts
   - measureProcessCapture12: "WARUM" - Grund oder Zweck des Prozessschritts

2. TABELLENERKENNUNG:
   - Wenn das Dokument eine tabellarische Form hat, behalte die Struktur der Zeilen bei
   - Jede Zeile wird zu einem eigenen Eintrag im "measureProcessCapture5" Array
   - Achte besonders auf die Spaltenzuordnung - jede Spalte entspricht einem bestimmten Feld
   - Bei Spaltenüberschriften wie "Wer", "Was", "Wie" usw. ordne sie entsprechend zu

3. UMGANG MIT LEEREN ZELLEN:
   - Wenn eine Zelle leer ist, verwende einen leeren String ("") für das entsprechende Feld
   - Fülle NICHT mit Platzhaltern oder vermeintlichen Informationen aus anderen Feldern auf
   - Behalte die Zuordnung jeder Spalte konsequent bei, auch wenn Zellen leer sind

4. ALLGEMEINE ANWEISUNGEN:
   - Wenn mehrere Prozessschritte erkennbar sind, erstelle für jeden einen separaten Eintrag
   - Alle Felder müssen in jedem Eintrag vorhanden sein, auch wenn sie leer sind
   - Verwende deutsche Begriffe und Beschreibungen
   - Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text oder Markdown
   - Bei unsicherer Zuordnung orientiere dich an der Bedeutung der Felder (WER, WAS, WIE, WO, WANN, WARUM)

5. BEI UNKLAREN DOKUMENTEN:
   - Falls keine klare Tabellenstruktur erkennbar ist, extrahiere so viele Prozessschritte wie möglich
   - Wenn gar keine Prozessinformationen erkennbar sind, gib ein Array mit einem leeren Objekt zurück

Analysiere das Bild jetzt und extrahiere die Prozessinformationen nach diesem Schema: