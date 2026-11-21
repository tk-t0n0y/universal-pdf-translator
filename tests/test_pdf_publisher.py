import os
import unittest
import fitz

from core.content_cleaner import PageContentCleaner, to_bengali_digits, to_english_digits
from core.book_builder import BookBuilder
from core.pdf_renderer import PDFRenderer

class TestPDFPublisher(unittest.TestCase):

    def test_bengali_digit_conversion(self):
        self.assertEqual(to_bengali_digits(12345), "১২৩৪৫")
        self.assertEqual(to_english_digits("১২৩৪৫"), "12345")

    def test_cleaner_metadata_extraction(self):
        sample_page_1 = """# দ্য ব্ল্যাক বুক অব পাওয়ার (The Black Book of Power)

> **পৃষ্ঠা ১ (Page 1) — প্রচ্ছদ শিরোনাম**  
> *পরিসংখ্যান*: মূল বাক্য: ১ | অনূদিত বাক্য: ১ | যাচাইকরণ: ✅ সম্পূর্ণ

---

# দ্য ব্ল্যাক বুক অব পাওয়ার
*(ক্ষমতার কৃষ্ণগ্রন্থ)*
"""
        parsed = PageContentCleaner.parse_page(sample_page_1, fallback_page_num=1)
        self.assertEqual(parsed["page_num"], 1)
        self.assertIn("প্রচ্ছদ শিরোনাম", parsed["chapter_title"])
        self.assertNotIn("পরিসংখ্যান", parsed["body_markdown"])
        self.assertIn("(ক্ষমতার কৃষ্ণগ্রন্থ)", parsed["body_markdown"])

    def test_cleaner_page_without_hr(self):
        sample_no_hr = """# দ্য ব্ল্যাক বুক অব পাওয়ার (The Black Book of Power)

পৃষ্ঠা ৪৩১ (Page 431) — অধ্যায় ১০: দ্য এনিমিস গিফট (The Enemy’s Gift)
পরিসংখ্যান: মূল বাক্য: ২৮ | স্থিতি: ✅ যাচাইকৃত (Verified)

লক্ষ্য করুন, এই পুরো অধ্যায় জুড়ে আপনার মন ঠিক কী করে এসেছে।
"""
        parsed = PageContentCleaner.parse_page(sample_no_hr, fallback_page_num=431)
        self.assertEqual(parsed["page_num"], 431)
        self.assertIn("অধ্যায় ১০", parsed["chapter_title"])
        self.assertNotIn("পরিসংখ্যান", parsed["body_markdown"])
        self.assertTrue(parsed["body_markdown"].startswith("লক্ষ্য করুন"))

    def test_book_builder_html(self):
        builder = BookBuilder(mode="1to1", include_cover=True, include_toc=True)
        css = builder.build_css()
        self.assertIn("KalpurushLocal", css)
        self.assertIn(".cover-page", css)
        self.assertIn(".page-sync", css)

    def test_pdf_renderer_small_sample(self):
        renderer = PDFRenderer()
        out_pdf = "output/test_unit_render.pdf"
        stats = renderer.render_range(
            start_page=1,
            end_page=3,
            output_pdf_path=out_pdf,
            mode="1to1",
            include_cover=False,
            include_toc=False
        )
        self.assertTrue(os.path.exists(out_pdf))
        self.assertGreater(stats["file_size_bytes"], 10000)
        self.assertEqual(stats["source_pages"], 3)
        self.assertEqual(stats["page_count"], 3)

        doc = fitz.open(out_pdf)
        extracted = doc[0].get_text()
        self.assertIn("কৃষ্ণগ্রন্থ", extracted)
        doc.close()

if __name__ == "__main__":
    unittest.main()
