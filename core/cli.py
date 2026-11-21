import argparse
import sys
import json
import os
from core.extractor import UniversalPDFExtractor
from core.verifier import MultiLingualVerifier
from core.tracker import TranslationTracker
from core.compiler import DocumentCompiler
from core.pdf_renderer import PDFRenderer

def run_cli():
    parser = argparse.ArgumentParser(description="Universal PDF Translation, Verification & Publishing CLI")
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

    # pdf subcommand (Publication Grade Typesetting & PDF Generation)
    pdf_parser = subparsers.add_parser("pdf", help="Render luxury publication-grade PDF book from translated pages")
    pdf_parser.add_argument("--pages-dir", default="translations/pages", help="Directory containing translated page markdowns")
    pdf_parser.add_argument("--mode", choices=["1to1", "book"], default="1to1", help="Pagination mode: 1to1 (exact page sync) or book (continuous editorial flow)")
    pdf_parser.add_argument("--range", dest="page_range", default=None, help="Page range to render (e.g. 1-25 or 1-100)")
    pdf_parser.add_argument("--volume", type=int, choices=[1, 2, 3, 4, 5, 6], default=None, help="Render a specific volume (1 to 6)")
    pdf_parser.add_argument("--volumes-all", action="store_true", help="Render all 6 volumes into individual PDFs")
    pdf_parser.add_argument("--all", action="store_true", help="Render the complete 933-page master book")
    pdf_parser.add_argument("--no-cover", action="store_true", help="Omit the cover page")
    pdf_parser.add_argument("--no-toc", action="store_true", help="Omit the table of contents")
    pdf_parser.add_argument("--out", default=None, help="Output PDF file path")
    pdf_parser.add_argument("--out-dir", default="output", help="Output directory when generating multiple volumes")

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

    elif args.command == "pdf":
        renderer = PDFRenderer(pages_dir=args.pages_dir)
        include_cover = not args.no_cover
        include_toc = not args.no_toc

        if args.volumes_all:
            os.makedirs(args.out_dir, exist_ok=True)
            print(f"Rendering all 6 Volumes to directory: {args.out_dir}")
            for vol_num, part in renderer.PARTS_MAP.items():
                safe_title = f"Volume_{vol_num}_Part_{vol_num}"
                out_path = os.path.join(args.out_dir, f"{safe_title}_{args.mode}.pdf")
                print(f"--> Building Volume {vol_num} (Pages {part['start']}-{part['end']})...")
                stats = renderer.render_volume(vol_num, out_path, mode=args.mode)
                print(f"    [OK] Generated {out_path} ({stats['page_count']} PDF pages, {stats['file_size_bytes']/1024:.1f} KB)")
            print("\nAll 6 volumes successfully generated!")

        elif args.volume is not None:
            part = renderer.PARTS_MAP[args.volume]
            out_path = args.out or os.path.join(args.out_dir, f"Volume_{args.volume}_{args.mode}.pdf")
            print(f"Rendering Volume {args.volume}: {part['title']} (Pages {part['start']}-{part['end']})...")
            stats = renderer.render_volume(args.volume, out_path, mode=args.mode)
            print(f"Successfully generated: {out_path}")
            print(f"  PDF Pages: {stats['page_count']}")
            print(f"  File Size: {stats['file_size_bytes']/1024:.1f} KB")

        elif args.all:
            out_path = args.out or os.path.join(args.out_dir, f"The_Black_Book_of_Power_Complete_{args.mode}.pdf")
            if args.mode == "1to1":
                stats = renderer.render_full_book(
                    output_pdf_path=out_path,
                    mode="1to1",
                    batch_size=100
                )
            else:
                print(f"Rendering Complete Book (Pages 1 to 933) in '{args.mode}' mode...")
                stats = renderer.render_range(
                    start_page=1,
                    end_page=933,
                    output_pdf_path=out_path,
                    mode=args.mode,
                    include_cover=include_cover,
                    include_toc=include_toc
                )
                print(f"Successfully generated: {out_path}")
                print(f"  PDF Pages: {stats['page_count']}")
                print(f"  File Size: {stats['file_size_bytes']/1024:.1f} KB")

        elif args.page_range:
            parts = args.page_range.split("-")
            start_p = int(parts[0])
            end_p = int(parts[1]) if len(parts) > 1 else start_p
            out_path = args.out or os.path.join(args.out_dir, f"Pages_{start_p:03d}_{end_p:03d}_{args.mode}.pdf")
            print(f"Rendering page range {start_p} to {end_p} in '{args.mode}' mode...")
            stats = renderer.render_range(
                start_page=start_p,
                end_page=end_p,
                output_pdf_path=out_path,
                mode=args.mode,
                include_cover=include_cover,
                include_toc=include_toc
            )
            print(f"Successfully generated: {out_path}")
            print(f"  PDF Pages: {stats['page_count']}")
            print(f"  File Size: {stats['file_size_bytes']/1024:.1f} KB")

        else:
            # Default preview of first chapter (pages 1 to 25)
            out_path = args.out or os.path.join(args.out_dir, f"Preview_Pages_001_025_{args.mode}.pdf")
            print(f"No range or volume specified. Generating default preview (Pages 1 to 25) in '{args.mode}' mode...")
            stats = renderer.render_range(
                start_page=1,
                end_page=25,
                output_pdf_path=out_path,
                mode=args.mode,
                include_cover=include_cover,
                include_toc=include_toc
            )
            print(f"Successfully generated preview: {out_path}")
            print(f"  PDF Pages: {stats['page_count']}")
            print(f"  File Size: {stats['file_size_bytes']/1024:.1f} KB")

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
