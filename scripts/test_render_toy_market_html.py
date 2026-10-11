"""Isolated regressions: python -B -m unittest scripts.test_render_toy_market_html.

REPORT/PAGES are mocked. All MD/HTML/media fixtures use TemporaryDirectory;
no real report content is read or written.
"""
from __future__ import annotations

import contextlib
import io
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from markdown_it import MarkdownIt
from PIL import Image

from scripts import render_toy_market_html as renderer


class Elements(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))

    def attrs(self, tag):
        return [attrs for name, attrs in self.nodes if name == tag]


class RendererTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="toy-market-render-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.report = self.root / "report"
        self.report.mkdir()
        self.pages = dict(renderer.PAGES)
        self.enterContext(patch.object(renderer, "REPORT", self.report))
        self.enterContext(patch.object(renderer, "PAGES", self.pages))
        for key, (label, _, _) in self.pages.items():
            links = "\n".join(
                f"[{info[0]}](./{name}.md#entry-{name})" for name, info in self.pages.items()
            )
            self.write_source(key, f"""# {label}：源标题不改

这是 **原始正文**，包含技术词 AI、中文与 40 个分析对象。

## 分组

<a id="entry-{key}"></a>

### 单款产品

{links}

[官方视频](https://example.org/watch?v=1&lang=zh)
裸链接 https://example.org/source?q=toy，保留原句。

| 项目 | 说明 |
| --- | --- |
| 状态 | 待核实 |
""")

    def write_source(self, key, text):
        (self.report / f"{key}.md").write_text(text, encoding="utf-8", newline="\n")

    def append_source(self, key, text):
        path = self.report / f"{key}.md"
        self.write_source(key, path.read_text(encoding="utf-8") + "\n" + text + "\n")

    def image(self, relative="media/g1/ad01.jpg", size=(640, 360)):
        path = self.report / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, (70, 100, 120)).save(path)
        return path

    def render_all(self):
        return {f"{key}.html": renderer.render_page(key) for key in self.pages}

    def run_main(self, *args):
        output = io.StringIO()
        with patch("sys.argv", ["render_toy_market_html.py", *args]), contextlib.redirect_stdout(output):
            renderer.main()
        return output.getvalue()

    def snapshot(self):
        return {
            path.relative_to(self.root): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in self.root.rglob("*") if path.is_file()
        }

    def test_four_page_routes_metadata_and_original_titles(self):
        self.assertEqual(list(self.pages), ["research", "competitors", "evidence", "product-atlas"])
        self.assertEqual(self.pages["product-atlas"][0], "产品图鉴")
        self.assertIn("41 个分析对象", self.pages["product-atlas"][1])
        self.assertIn("非41款已售", self.pages["product-atlas"][1])
        self.assertEqual(self.pages["evidence"][1], "分级证据 · 技术与产品来源")
        pages = self.render_all()
        links, tables = renderer.validate(pages)
        self.assertGreater(links, 0)
        self.assertEqual(tables, 4)
        for key, (label, _, _) in self.pages.items():
            markup = pages[f"{key}.html"]
            self.assertIn(f"<h1>{label}：源标题不改</h1>", markup)
            nav = re.search(r'<nav class="page-nav"[^>]*>(.*?)</nav>', markup, re.S).group(1)
            anchors = Elements(nav).attrs("a")
            self.assertEqual([a["href"] for a in anchors], list(pages))
            self.assertEqual([a["href"] for a in anchors if a.get("aria-current") == "page"], [f"{key}.html"])

    def test_forty_cards_have_toc_targets_and_preserve_explicit_anchors(self):
        source = '# 逐产品图鉴\n\n<a id="entry-product-atlas"></a>\n\n'
        for group in range(4):
            source += f"## 第 {group + 1} 组\n\n"
            for index in range(group * 10 + 1, group * 10 + 11):
                source += f'<a id="card-ad{index:02}"></a>\n\n### AD{index:02} 产品\n\n卡片正文 {index}。\n\n'
        self.write_source("product-atlas", source)
        pages = self.render_all()
        renderer.validate(pages)
        markup = pages["product-atlas.html"]
        nodes = Elements(markup)
        h3s = nodes.attrs("h3")
        self.assertEqual(len(h3s), 40)
        hrefs = [attrs["href"] for attrs in nodes.attrs("a") if "href" in attrs]
        for attrs in h3s:
            self.assertIn("#" + attrs["id"], hrefs)
        for index in range(1, 41):
            self.assertIn(f'<a id="card-ad{index:02}"></a>', markup)

    def test_local_image_dimensions_loading_and_source_preserved(self):
        self.image()
        self.append_source("product-atlas", "![产品正面图](media/g1/ad01.jpg)")
        pages = self.render_all()
        renderer.validate(pages)
        attrs = Elements(pages["product-atlas.html"]).attrs("img")[0]
        self.assertEqual(attrs, {"src": "media/g1/ad01.jpg", "alt": "产品正面图", "loading": "lazy", "decoding": "async", "width": "640", "height": "360"})

    def test_percent_encoded_image_with_query_and_fragment(self):
        self.image("media/g1/产品 图.jpg", (25, 70))
        self.append_source("product-atlas", '![侧面](media/g1/%E4%BA%A7%E5%93%81%20%E5%9B%BE.jpg?v=1&mode=full#view)')
        pages = self.render_all()
        renderer.validate(pages)
        attrs = Elements(pages["product-atlas.html"]).attrs("img")[0]
        self.assertEqual(attrs["width"], "25")
        self.assertEqual(attrs["height"], "70")
        self.assertIn("?v=1&mode=full#view", attrs["src"])

    def test_missing_image_not_hidden_and_validation_fails(self):
        self.append_source("product-atlas", "![尚未归档的产品图](media/g1/missing.jpg)")
        pages = self.render_all()
        attrs = Elements(pages["product-atlas.html"]).attrs("img")[0]
        self.assertEqual(attrs["src"], "media/g1/missing.jpg")
        self.assertEqual(attrs["alt"], "尚未归档的产品图")
        self.assertEqual(attrs["loading"], "lazy")
        self.assertEqual(attrs["decoding"], "async")
        self.assertNotIn("width", attrs)
        with self.assertRaisesRegex(AssertionError, r"product-atlas.html: Missing image"):
            renderer.validate(pages)

    def test_directory_is_not_an_image(self):
        (self.report / "media/g1").mkdir(parents=True)
        with self.assertRaisesRegex(AssertionError, "not a file"):
            renderer.validate({"sample.html": '<img src="media/g1">'})

    def test_outside_media_and_invalid_local_paths_rejected(self):
        (self.report / "outside.jpg").write_bytes(b"not media")
        (self.root / "outside.jpg").write_bytes(b"not in report")
        (self.report / "media-other").mkdir()
        (self.report / "media-other/ad01.jpg").write_bytes(b"sibling")
        sources = [
            "outside.jpg", "../outside.jpg", "media/../outside.jpg",
            "media/%2e%2e/outside.jpg", "media/%2e%2e/%2e%2e/outside.jpg",
            "media-other/ad01.jpg", "/media/g1/ad01.jpg",
            r"media\..\outside.jpg", "media/%5c../outside.jpg", "media/g1/ad01.jpg%00",
            "media/g1/ad01.jpg%0A", "media/g1/ad01.jpg:stream", "",
        ]
        for src in sources:
            with self.subTest(src=src), self.assertRaises(AssertionError):
                renderer.validate({"sample.html": f'<img src="{src}">'})
        with self.assertRaisesRegex(AssertionError, "Invalid image src"):
            renderer.validate({"sample.html": "<img alt='no src'>"})

    def test_symlink_cannot_escape_media(self):
        outside = self.root / "external.jpg"
        Image.new("RGB", (10, 10)).save(outside)
        link = self.report / "media/linked.jpg"
        link.parent.mkdir()
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        with self.assertRaisesRegex(AssertionError, "outside media"):
            renderer.validate({"sample.html": '<img src="media/linked.jpg">'})

    def test_media_root_symlink_cannot_escape_report(self):
        outside = self.root / "external-media"
        outside.mkdir()
        Image.new("RGB", (10, 10)).save(outside / "photo.jpg")
        try:
            (self.report / "media").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        with self.assertRaisesRegex(AssertionError, "outside media"):
            renderer.validate({"sample.html": '<img src="media/photo.jpg">'})

    def test_unsafe_images_are_never_opened_for_dimensions(self):
        for src in ["https://example.org/photo.jpg", "../outside.jpg", "media/missing.jpg"]:
            with self.subTest(src=src), patch.object(renderer.Image, "open") as image_open:
                self.write_source("product-atlas", f"# 标题\n\n![图片]({src})\n")
                markup = renderer.render_page("product-atlas")
                self.assertEqual(len(Elements(markup).attrs("img")), 1)
                image_open.assert_not_called()

    def test_validation_uses_actual_html_image_src_including_raw_html(self):
        self.image()
        self.append_source("product-atlas", '<img src="media/g1/ad01.jpg?x=1&amp;y=2" alt="原始 HTML">')
        pages = self.render_all()
        renderer.validate(pages)
        pages["product-atlas.html"] = pages["product-atlas.html"].replace("media/g1/ad01.jpg", "media/g1/not-present.jpg")
        with self.assertRaisesRegex(AssertionError, "not-present.jpg"):
            renderer.validate(pages)

    def test_remote_images_and_other_assets_rejected_but_links_allowed(self):
        self.image()
        assets = [
            '<img src="https://example.org/a.jpg">', '<img src="//example.org/a.jpg">',
            '<img src="HTTP://example.org/a.jpg">', '<img src="ftp://example.org/a.jpg">',
            '<img src="data:image/png;base64,AAAA">', '<img src="file:///C:/a.jpg">',
            '<img src="blob:https://example.org/id">', '<img src="https://[bad">',
            r'<img src="\\example.org\a.jpg">',
            '<iframe src="https://example.org/embed"></iframe>',
            '<script src="https://example.org/app.js"></script>',
            '<link rel="stylesheet" href="https://example.org/app.css">',
            '<video poster="https://example.org/poster.jpg"></video>',
            '<audio src="https://example.org/voice.mp3"></audio>',
            '<source src="https://example.org/video.mp4">',
            '<source srcset="media/g1/ad01.jpg 1x, //example.org/a.jpg 2x">',
            '<img src="media/g1/ad01.jpg" srcset="https://example.org/a.jpg 2x">',
            '<base href="https://example.org/">',
        ]
        for markup in assets:
            with self.subTest(markup=markup), self.assertRaisesRegex(AssertionError, "Remote assets"):
                renderer.validate({"sample.html": markup})
        renderer.validate({"sample.html": '<a href="https://example.org/watch">官方视频外链</a>'})

    def test_pillow_unsupported_local_image_is_kept_without_fake_dimensions(self):
        path = self.report / "media/shape.svg"
        path.parent.mkdir()
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10"></svg>', encoding="utf-8")
        self.append_source("product-atlas", "![本地矢量图](media/shape.svg)")
        pages = self.render_all()
        renderer.validate(pages)
        attrs = Elements(pages["product-atlas.html"]).attrs("img")[0]
        self.assertEqual(attrs["loading"], "lazy")
        self.assertNotIn("width", attrs)
        self.assertNotIn("height", attrs)

    def test_source_body_text_and_alt_text_preserved(self):
        self.image()
        self.append_source("research", "~~删除线示例~~、`https://example.org/code`，仍是正文。\n\n![**强调**与图注](media/g1/ad01.jpg)")
        source = (self.report / "research.md").read_text(encoding="utf-8")
        md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
        original = md.renderer.render(md.parse(source)[3:], md.options, {})
        markup = renderer.render_page("research")
        article = re.search(r'<article class="prose">(.*?)</article>', markup, re.S).group(1)
        self.assertEqual(renderer.visible_text(original), renderer.visible_text(article))
        self.assertEqual(Elements(original).attrs("img")[0]["alt"], Elements(article).attrs("img")[0]["alt"])
        self.assertIn('class="table-scroll" tabindex="0"', article)

    def test_link_rewriting_queries_anchors_and_external_rel(self):
        self.assertEqual(renderer.rewrite_link("./product-atlas.md?v=2#card-ad01"), "./product-atlas.html?v=2#card-ad01")
        self.assertEqual(renderer.rewrite_link("product-atlas.md#card-ad01"), "product-atlas.html#card-ad01")
        for href in ["other.md", "#local", "https://example.org/product-atlas.md#card-ad01", "//example.org/research.md"]:
            self.assertEqual(renderer.rewrite_link(href), href)
        markup = renderer.render_page("research")
        anchors = Elements(markup).attrs("a")
        external = [a for a in anchors if a.get("href", "").startswith("https://")]
        self.assertEqual(len(external), 2)
        for anchor in external:
            self.assertEqual(anchor["target"], "_blank")
            self.assertEqual(anchor["rel"], "noopener noreferrer")
        self.assertIn('<a id="entry-research"></a>', markup)
        self.assertIn('href="./product-atlas.html#entry-product-atlas"', markup)

    def test_missing_link_and_anchor_fail_validation(self):
        for href, message in [("missing.html", "Missing file"), ("research.html#missing", "Missing anchor")]:
            with self.subTest(href=href):
                pages = self.render_all()
                pages["research.html"] += f'<a href="{href}">无效目标</a>'
                with self.assertRaisesRegex(AssertionError, message):
                    renderer.validate(pages)

    def test_duplicate_ids_are_rejected(self):
        self.append_source("product-atlas", '<a id="entry-product-atlas"></a>')
        with self.assertRaisesRegex(AssertionError, "Duplicate IDs"):
            renderer.validate(self.render_all())
        with self.assertRaisesRegex(AssertionError, "Duplicate IDs"):
            renderer.validate({"sample.html": '<a id="card-ad01"></a><h3 id="card-ad01">重复</h3>'})

    def test_encoding_replacement_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Encoding replacement"):
            renderer.validate({"sample.html": "<p>\ufffd</p>"})

    def test_render_is_deterministic_and_never_writes(self):
        self.image()
        self.append_source("product-atlas", "![图](media/g1/ad01.jpg)")
        before = self.snapshot()
        self.assertEqual(self.render_all(), self.render_all())
        self.assertEqual(before, self.snapshot())

    def test_check_succeeds_without_writing_and_reports_dynamic_page_count(self):
        self.image()
        self.append_source("product-atlas", "![图](media/g1/ad01.jpg)")
        self.assertIn("PASS: 4 pages;", self.run_main())
        before = self.snapshot()
        output = self.run_main("--check")
        self.assertIn("PASS: 4 pages;", output)
        self.assertEqual(output.count("CHECK "), 4)
        self.assertEqual(before, self.snapshot())
        with patch.object(renderer, "PAGES", {"research": self.pages["research"]}):
            self.write_source("research", "# 单页\n\n正文\n")
            self.assertIn("PASS: 1 pages;", self.run_main())

    def test_check_missing_or_stale_html_does_not_write(self):
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "Missing HTML"):
            self.run_main("--check")
        self.assertEqual(before, self.snapshot())
        self.run_main()
        (self.report / "product-atlas.html").write_text("stale", encoding="utf-8")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "Stale HTML"):
            self.run_main("--check")
        self.assertEqual(before, self.snapshot())

    def test_check_missing_atlas_markdown_does_not_write(self):
        (self.report / "product-atlas.md").unlink()
        before = self.snapshot()
        with self.assertRaises(FileNotFoundError):
            self.run_main("--check")
        self.assertEqual(before, self.snapshot())

    def test_check_invalid_image_does_not_write(self):
        self.run_main()
        self.append_source("product-atlas", "![缺图](media/missing.jpg)")
        before = self.snapshot()
        with self.assertRaisesRegex(AssertionError, "Missing image"):
            self.run_main("--check")
        self.assertEqual(before, self.snapshot())

    def test_resolved_escape_rejected_without_symlink_privileges(self):
        report = self.report.resolve()
        for outside in [self.root / "external.jpg", self.report / "media-other/photo.jpg"]:
            with self.subTest(outside=outside):
                with patch.object(Path, "resolve", side_effect=[report, outside.resolve()]):
                    with patch.object(Path, "is_file") as is_file:
                        with self.assertRaisesRegex(AssertionError, "outside media"):
                            renderer.local_image_path("media/linked.jpg")
                        is_file.assert_not_called()

    def test_duplicate_src_uses_browser_first_attribute(self):
        self.image()
        with self.assertRaisesRegex(AssertionError, "Remote assets"):
            renderer.validate({"sample.html": '<img src="https://example.org/a.jpg" src="media/g1/ad01.jpg">'})
        with self.assertRaisesRegex(AssertionError, "Missing image"):
            renderer.validate({"sample.html": '<img src="media/missing.jpg" src="media/g1/ad01.jpg">'})

    def test_protocol_relative_external_link_rel(self):
        self.append_source("research", "[video](//example.org/watch)")
        anchors = Elements(renderer.render_page("research")).attrs("a")
        external = next(attrs for attrs in anchors if attrs.get("href") == "//example.org/watch")
        self.assertEqual(external["target"], "_blank")
        self.assertEqual(external["rel"], "noopener noreferrer")

    def test_mobile_navigation_image_and_print_css_guards(self):
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", renderer.CSS)
        self.assertIn(".prose{overflow-wrap:anywhere;min-width:0}", renderer.CSS)
        self.assertIn(".reading{min-width:0", renderer.CSS)
        self.assertIn("max-height:420px;object-fit:contain", renderer.CSS)
        print_css = renderer.CSS.split("@media print", 1)[1]
        self.assertIn(".prose img{max-width:100%;max-height:220mm;width:auto;height:auto;object-fit:contain;break-inside:avoid;page-break-inside:avoid}", print_css)
        self.assertNotIn("overflow:hidden", print_css)


if __name__ == "__main__":
    unittest.main()
