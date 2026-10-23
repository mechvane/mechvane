# Quellenprüfung Lauf 2 (2026-10-21)

Befehl: `python3 tools/check_sources.py --json docs/research/2026-10-21-{passungen-toleranzen,waelzlager-einbau,wellen-sicherungsringe,blech,spritzguss,oring-nuten}-flash.md`

| Datei | Einträge mit Zitat | Zitat teilweise | Zitat nicht gefunden | Zahlen gefunden |
|---|---|---|---|---|
| passungen-toleranzen | 7 | 2 | 5 | 48/72 |
| waelzlager-einbau | 6 | 2 | 4 | 10/42 |
| wellen-sicherungsringe | 4 | 2 | 2 | 37/44 |
| blech | 8 | 1 | 7 | 23/68 |
| spritzguss | 6 | 1 | 5 | 34/62 |
| oring-nuten | 8 | 0 | 8 | 75/100 |

Kein Zitat ist voll bestätigt, von 388 Zahlen sind 227 gefunden (59 %). Die „wörtlichen
Zitate“ von Flash sind überwiegend Umschreibungen. Werte gelten erst als belegt, wenn das
Skript sie in der Quelle findet oder eine zweite Quelle sie bestätigt. Am schwächsten belegt
ist der Wälzlager-Einbau (Kataloge sind meist JavaScript-Seiten oder große PDFs).
