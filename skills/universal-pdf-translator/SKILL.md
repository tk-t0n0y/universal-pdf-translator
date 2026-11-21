---
name: universal-pdf-translator
description: "Universal autonomous agent skill for high-fidelity, zero-omission PDF document and book translation with programmatic sentence verification."
---

# Universal PDF Translator Agent Skill

## Overview
This skill provides an autonomous agent with the exact workflow, commands, and verification criteria to translate books, research papers, and documents page-by-page from PDF to any target language without omitting a single sentence.

---

## Agent Execution Loop

For each page $P \in [1, N]$:

### Step 1: Extract Source Text
Run the universal extractor to obtain structured JSON with sentence segmentation:
```bash
python main.py extract <PDF_PATH> <PAGE_NUM> --out data/source_page_<PAGE_NUM>.json
```

### Step 2: Formulate Translation
- Read the extracted source JSON (`sentences` array and `raw_text`).
- Consult the project's master prompts in `prompts/`.
- Translate every sentence with semantic fidelity and rich style into the target language.
- Ensure proper sentence termination marks (e.g., Bengali `।`, Hindi `।`, Japanese `。`, English `.`).

### Step 3: Write Markdown File
Write the translated page to `pages/page_<PAGE_NUM>.md` including frontmatter:
```markdown
---
page: <PAGE_NUM>
source_sentences: <SRC_COUNT>
translated_sentences: <TR_COUNT>
coverage_ratio: <RATIO>
status: "DRAFT"
---

<TRANSLATED_BODY_TEXT>
```

### Step 4: Run Verification Engine
Execute the programmatic verifier:
```bash
python main.py verify <PDF_PATH> <PAGE_NUM> pages/page_<PAGE_NUM>.md --lang <TARGET_LANG>
```

### Step 5: Check Status & Loop
- If the output JSON shows `"status": "VERIFIED"` and `"coverage_ratio" >= 1.0`, update the frontmatter status to `"VERIFIED"`.
- If `"FLAGGED_INCOMPLETE"`, inspect the missing sentences, enhance the translation, and re-verify.
- Move to page $P + 1$.

---

## Final Assembly
Once all pages are verified, assemble the final master document:
```bash
python main.py compile --pages-dir pages --output compiled_document.md
```
