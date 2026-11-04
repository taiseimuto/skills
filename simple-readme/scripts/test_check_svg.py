"""Run with: python3 -m unittest discover -s scripts -p 'test_*.py'."""

from pathlib import Path
import tempfile
import unittest

from check_svg import check_svg

START = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"
 role="img" aria-labelledby="t d"><title id="t">A flow</title>
 <desc id="d">Input becomes output.</desc>'''


class SvgChecks(unittest.TestCase):
    def check(self, extra="", start=START):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "diagram.svg"
            path.write_text(start + extra + "</svg>", encoding="utf-8")
            return check_svg(path)

    def test_embedded_vectors_and_local_markers_pass(self):
        self.assertEqual(self.check('''<defs><marker id="m"/><symbol id="logo">
          <path d="M0 0"/></symbol></defs><use href="#logo"/>
          <path marker-end="url(#m)" d="M0 0L1 1"/>'''), [])

    def test_missing_logo_reference_fails(self):
        self.assertTrue(any("Unresolved" in e for e in self.check('<use href="#missing"/>')))

    def test_external_logo_fails(self):
        self.assertTrue(any("Nonlocal href" in e for e in self.check(
            '<image href="https://example.org/logo.svg"/>')))

    def test_external_css_and_inline_resources_fail(self):
        for extra in ['<style>.x{fill:url(https://example.org/f.svg)}</style>',
                      '<style>@import "https://example.org/x.css";</style>',
                      '<path style="filter:url(https://example.org/f.svg)"/>']:
            with self.subTest(extra=extra):
                self.assertTrue(self.check(extra))

    def test_duplicate_ids_fail(self):
        self.assertTrue(any("Duplicate" in e for e in self.check('<path id="t"/>')))

    def test_empty_accessible_description_fails(self):
        self.assertTrue(self.check(start=START.replace("Input becomes output.", "")))

    def test_active_content_fails(self):
        for extra in ['<script/>', '<g onload="alert(1)"/>', '<foreignObject/>']:
            with self.subTest(extra=extra):
                self.assertTrue(self.check(extra))

    def test_invalid_xml_and_missing_file_fail(self):
        self.assertTrue(self.check('<g>'))
        with tempfile.TemporaryDirectory() as folder:
            self.assertTrue(check_svg(Path(folder) / "missing.svg"))

    def test_starter_is_accepted(self):
        starter = Path(__file__).resolve().parents[1] / "assets/flow-starter.svg"
        self.assertEqual(check_svg(starter), [])


if __name__ == "__main__":
    unittest.main()
