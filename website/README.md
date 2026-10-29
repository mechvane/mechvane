# Website (mechvane.dev)

Statische Seite, Entwurf von Gemini 4 Argon nach `docs/website/ARGON-PROMPT.md`, eingebaut und geprüft
von Claude. Wird von `tools/build_demo_site.py` an die Wurzel der Pages-Seite kopiert:

- `/` diese Website (`website/index.html`, `website/assets/`)
- `/media/` Bilder aus `docs/media/`
- `/demo/` die bisherige Live-Demo (Prüfseite, „Model by hand“)
- `/roadmap/` die Roadmap-Seite (`tools/roadmap_page.html`, liest `roadmap.json` live)

Entwurf von Argon (Issue #20, über agy, 8 % Argon-Wochenkontingent), von Claude geprüft: Grauguss-Einschraubtiefe
auf 1,0 × d korrigiert (Tabelle), Open-Graph-Bild absolut. Alte Demo-Adressen leiten weiter (`/model.html`).
