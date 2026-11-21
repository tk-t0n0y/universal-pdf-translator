# Universal PDF Translator

A modular open-source toolkit and agent skill for high-fidelity PDF translation with zero omission.

## Features

- **Universal Extractor**: Extracts text from any PDF with sentence-level segmentation.
- **Multilingual Verifier**: Programmatically verifies translated text against source sentence counts using target-language delimiters.
- **Progress Tracker**: Generates JSON and Markdown tracking reports.
- **Compiler**: Assembles translated pages into a unified document.
- **Agent Skill**: Conforms to agent skill standards for autonomous AI translation workflows.

## Quickstart

```bash
pip install -r requirements.txt
```

### Extract a page
```bash
python main.py extract input.pdf 1 --out data/page_001.json
```

### Verify a translated page
```bash
python main.py verify input.pdf 1 pages/page_001.md --lang bengali
```

### Compile all translated pages
```bash
python main.py compile --pages-dir pages --output compiled.md
```

## License

MIT License
