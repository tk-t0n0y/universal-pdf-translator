import os
import json

class TranslationTracker:
    """Maintains project-wide progress tracking in JSON and Markdown formats."""

    def __init__(self, json_path: str, md_path: str):
        self.json_path = json_path
        self.md_path = md_path

    def load_tracker(self) -> dict:
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def record_page(self, record: dict) -> dict:
        tracker = self.load_tracker()
        page_key = str(record["page_num"])
        tracker[page_key] = record

        os.makedirs(os.path.dirname(os.path.abspath(self.json_path)), exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(tracker, f, ensure_ascii=False, indent=2)

        self.generate_markdown(tracker)
        return tracker

    def generate_markdown(self, tracker: dict):
        lines = [
            "# Universal Translation Project — Master Progress Tracker",
            "",
            "> **Policy**: Zero-Omission Sentence Fidelity. Every page verified programmatically.",
            "",
            "| Page | Source Sentences | Source Words | Translated Sentences | Translated Words | Ratio | Status | Timestamp |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        sorted_keys = sorted(tracker.keys(), key=lambda x: int(x))
        verified_count = 0
        for k in sorted_keys:
            r = tracker[k]
            status_text = "VERIFIED" if r.get("status") == "VERIFIED" else "FLAGGED"
            badge = "✅ Verified" if status_text == "VERIFIED" else "⚠️ Flagged"
            if status_text == "VERIFIED":
                verified_count += 1
            ts = r.get("verified_at", "")[:19]
            lines.append(
                f"| **Page {r['page_num']}** | {r.get('source_sentences', 0)} | {r.get('source_words', 0)} | "
                f"{r.get('translated_sentences', 0)} | {r.get('translated_words', 0)} | {r.get('coverage_ratio', 0.0)} | {badge} | {ts} |"
            )

        lines.append("")
        lines.append(f"**Total Pages Tracked**: {len(tracker)} | **Verified Pages**: {verified_count}")

        os.makedirs(os.path.dirname(os.path.abspath(self.md_path)), exist_ok=True)
        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
