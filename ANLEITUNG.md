# EDEKA Mühlenbein – Promo Studio

Erstelle professionelle Aktionsmotive (Instagram-Post, Story und Plakate A4/A5)
in wenigen Sekunden – mit dem Waschbär-Branding, deinen Produktfotos und in 4K-Qualität.

Die App läuft **lokal auf deinem Rechner**. Es ist keine Installation von
Python o. Ä. nötig – du startest einfach eine Datei, und die App öffnet sich
im Browser.

---

## 1. Installation

### Windows
1. Ordner `edeka-promo-tool-windows` entpacken.
2. Doppelklick auf **`edeka-promo-tool.exe`**.
3. Beim ersten Start fragt Windows ggf. nach („Windows hat den PC geschützt“) →
   **„Weitere Informationen“ → „Trotzdem ausführen“** (die App ist sicher, nur
   nicht kostenpflichtig signiert).
4. Die App öffnet sich automatisch im Browser unter `http://localhost:8000`.
5. Zum Beenden das schwarze Konsolenfenster schließen.

### macOS
1. `edeka-promo-tool.app` in den Ordner **Programme** ziehen.
2. Beim ersten Start: **Rechtsklick → „Öffnen“ → „Öffnen“** (einmalig, weil die
   App nicht über den App Store kommt).
3. Die App öffnet sich im Browser unter `http://localhost:8000`.

### Linux
1. Paket entpacken:
   ```bash
   tar -xzf edeka-promo-tool-linux.tar.gz
   cd edeka-promo-tool-linux
   ```
2. Installieren:
   ```bash
   ./install.sh
   ```
3. **„EDEKA Promo Tool“** im Anwendungsmenü öffnen (oder im Terminal
   `edeka-promo-tool` ausführen). Die App öffnet sich im Browser.

---

## 2. Benutzung

1. **Briefing ausfüllen**: Produkt, Preis, optional „statt“-Preis,
   Aktionszeitraum (z. B. „nur heute“, „KW 24“, „bis 22.06.“), Herkunft, Claim.
2. **Produktbild / Motiv** wählen:
   - *Automatisch* (nach Produktname),
   - ein **integriertes Motiv** (Erdbeeren, Tomaten …) oder
   - ein **eigenes Foto** (siehe „Eigene Produkte“).
3. **Designstil** wählen – jede Option zeigt ein Beispiel mit deinen Eingaben:
   EDEKA Style, Dark Luxe, Editorial, Color Block, Foto Lifestyle, Magazin, Retro.
4. **Tonalität** (Stimmung) und **Kreativniveau** (Intensität) einstellen.
5. **Format** wählen: Post (1:1), Story (9:16), Plakat A4 oder A5.
6. **„Promotion erstellen & exportieren“** klicken → die fertige Promotion
   erscheint.
7. Mit **„Als … herunterladen“** das Bild im gewählten Format speichern (4K, PNG).

### Eigene Produkte hochladen
- Oben rechts auf **„Produkte“** klicken.
- Foto hochladen (am besten mit weißem oder transparentem Hintergrund),
  Name + Kategorie angeben → speichern.
- Das Produkt steht danach im Motiv-Auswahlmenü zur Verfügung. Der Hintergrund
  wird automatisch entfernt.

### KI-Einstellungen (optional)
- Unter **„KI-Einstellungen“** kann ein API-Key (OpenRouter o. ä.) hinterlegt
  werden. Damit werden Texte/Vorschläge KI-optimiert.
- **Ohne Key** funktioniert die App vollständig im lokalen Profi-Modus.
- Der Key wird **nur lokal** auf diesem Gerät gespeichert.

---

## 3. Wo werden Daten gespeichert?

Eigene Produkte, Einstellungen und exportierte Bilder liegen im
Benutzerverzeichnis (bleiben bei Updates erhalten):

- **Windows:** `%LOCALAPPDATA%\EDEKA Promo Tool`
- **macOS:** `~/Library/Application Support/EDEKA Promo Tool`
- **Linux:** `~/.local/share/edeka-promo-tool`

---

## 4. Hilfe

- **Die App öffnet sich nicht im Browser:** manuell `http://localhost:8000`
  aufrufen.
- **„Port belegt“ / startet nicht:** evtl. läuft die App schon. Vorhandenes
  Fenster schließen und neu starten.
- **Bild lädt nicht:** Seite neu laden (F5).

Kontakt: EDEKA Mühlenbein · Wolfsangerstr. 100 · 34125 Kassel ·
Instagram **@waschbaer_edeka**
