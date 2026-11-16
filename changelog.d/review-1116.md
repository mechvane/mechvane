Fixed

- Parts list: a missing or unreadable part file gives a row marked "(file missing)" or "(unreadable)" instead of failing the whole list; CSV cells that start with = + - or @ are no longer run as formulas by spreadsheets. (#49)
- "Last step": a changed sketch dimension or parameter now shows up in the bar and the ghost, and the first step in the live demo marks only what it added. (#121)
- Findings keep their rule's link as a source when the knowledge catalog is not available (pip installs); a held Ctrl+Z no longer queues dozens of undos. (#120, #112)
