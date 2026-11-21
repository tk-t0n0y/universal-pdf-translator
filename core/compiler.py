import os
import glob
import re

class DocumentCompiler:
    """Assembles individual translated page markdown files into a single unified book or document."""

    def __init__(self, pages_dir: str, output_path: str):
        self.pages_dir = pages_dir
        self.output_path = output_path

    @staticmethod
    def strip_frontmatter(content: str) -> str:
        """Removes yaml frontmatter metadata blocks."""
        pattern = r'^---\s*\n.*?\n---\s*\n'
        return re.sub(pattern, '', content, flags=re.DOTALL)

    def compile(self) -> str:
        md_files = glob.glob(os.path.join(self.pages_dir, "page_*.md"))
        if not md_files:
            return ""

        def extract_page_id(filepath):
            filename = os.path.basename(filepath)
            match = re.search(r'page_(\d+)', filename)
            return int(match.group(1)) if match else 0

        md_files.sort(key=extract_page_id)

        compiled_parts = []
        for fpath in md_files:
            p_id = extract_page_id(fpath)
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
            body = self.strip_frontmatter(raw).strip()
            if body:
                compiled_parts.append(f"<!-- Page {p_id} -->\n\n{body}\n\n---\n")

        full_doc = "\n".join(compiled_parts)
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as out:
            out.write(full_doc)

        return self.output_path
