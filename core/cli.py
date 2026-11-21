import argparse
import sys
import json
import os
from core.extractor import UniversalPDFExtractor
from core.verifier import MultiLingualVerifier
from core.tracker import TranslationTracker
from core.compiler import DocumentCompiler

def run_cli():
    parser = argparse.ArgumentParser(description="Universal PDF Translation & Verification CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # extract subcommand
    extract_parser = subparsers.add_parser("extract", help="Extract text and sentences from PDF page")
    extract_parser.add_argument("pdf", help="Path to input PDF file")
    extract_parser.add_argument("page", type=int, help="Page number (1-based)")
    extract_parser.add_argument("--out", default=None, help="Optional output JSON path")

    # verify subcommand
    verify_parser = subparsers.add_parser("verify", help="Verify translated page against PDF source")
    verify_parser.add_argument("pdf", help="Path to input PDF file")
    verify_parser.add_argument("page", type=int, help="Page number (1-based)")
    verify_parser.add_argument("trans_file", help="Path to translated markdown file")
    verify_parser.add_argument("--lang", default="bengali", help="Target language (bengali, hindi, cjk, general)")
    verify_parser.add_argument("--tracker-json", default="translations/tracker.json", help="Path to tracker JSON")
    verify_parser.add_argument("--tracker-md", default="translations/master_tracker.md", help="Path to master tracker MD")

    # compile subcommand
    compile_parser = subparsers.add_parser("compile", help="Compile translated page files into single document")
    compile_parser.add_argument("--pages-dir", default="translations/pages", help="Directory containing translated page markdowns")
    compile_parser.add_argument("--output", default="translations/compiled_book.md", help="Output compiled markdown path")

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Display translation progress overview")
    status_parser.add_argument("--tracker-json", default="translations/tracker.json", help="Path to tracker JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "extract":
        extractor = UniversalPDFExtractor(args.pdf)
        data = extractor.extract_page(args.page)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.command == "verify":
        extractor = UniversalPDFExtractor(args.pdf)
        source_data = extractor.extract_page(args.page)

        if not os.path.exists(args.trans_file):
            print(f"Error: Translation file not found at {args.trans_file}", file=sys.stderr)
            sys.exit(1)

        with open(args.trans_file, "r", encoding="utf-8") as f:
            trans_content = f.read()

        verifier = MultiLingualVerifier(target_lang=args.lang)
        result = verifier.verify(args.page, source_data, trans_content)

        tracker = TranslationTracker(args.tracker_json, args.tracker_md)
        tracker.record_page(result)

        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "compile":
        compiler = DocumentCompiler(args.pages_dir, args.output)
        out = compiler.compile()
        print(f"Successfully compiled pages to: {out}")

    elif args.command == "status":
        tracker_mgr = TranslationTracker(args.tracker_json, "dummy.md")
        data = tracker_mgr.load_tracker()
        total = len(data)
        verified = sum(1 for v in data.values() if v.get("status") == "VERIFIED")
        flagged = sum(1 for v in data.values() if v.get("status") != "VERIFIED")
        print(f"Total Tracked: {total}")
        print(f"Verified: {verified} ({ (verified/total*100) if total > 0 else 0:.1f}%)")
        print(f"Flagged: {flagged}")

if __name__ == "__main__":
    run_cli()
