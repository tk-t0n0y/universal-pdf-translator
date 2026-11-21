# Master Translation Prompts

This directory provides production-tested prompt architectures for LLMs and autonomous agents performing large-scale PDF translations.

| File | Target Use Case | Key Strength |
| :--- | :--- | :--- |
| `zero_omission_prompt.md` | Universal Baseline | Strict 1:1 semantic and sentence fidelity |
| `literary_bengali_prompt.md` | Bengali Literary & Philosophy | High psychological depth, elegant diction |
| `technical_prompt.md` | STEM & Academic Papers | Terminology consistency, equations/code preservation |

### How to Use With LLMs
When translating a single page or chunk:
1. Pass the relevant prompt as the **System Prompt**.
2. Supply the source text (extracted via `main.py extract <pdf> <page>`).
3. Save the translated output as `page_<NUM>.md`.
4. Run `main.py verify` to programmatically validate the coverage ratio.
