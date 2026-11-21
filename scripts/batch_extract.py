import sys
import os
import json
from core.extractor import UniversalPDFExtractor

def batch_extract(pdf_path: str, start_page: int, end_page: int, out_dir: str = "data"):
    """Extracts a range of pages from a PDF into JSON files."""
    extractor = UniversalPDFExtractor(pdf_path)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Extracting pages {start_page} to {end_page} from {pdf_path} into {out_dir}/...")

    for p in range(start_page, end_page + 1):
        data = extractor.extract_page(p)
        out_file = os.path.join(out_dir, f"source_page_{p:03d}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print("Batch extraction complete.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python batch_extract.py <pdf_path> <start_page> <end_page> [out_dir]")
        sys.exit(1)
    pdf = sys.argv[1]
    s_p = int(sys.argv[2])
    e_p = int(sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else "data"
    batch_extract(pdf, s_p, e_p, out)
