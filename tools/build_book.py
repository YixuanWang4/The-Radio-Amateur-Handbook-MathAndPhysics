#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build every chapter to DOCX, then compile the book with a static TOC."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md2docx  # noqa: E402
from pdf_outline import extract  # noqa: E402

CHAPTER_RE = re.compile(r"^(0[1-9]|1[0-9]|2[0-5])-")
def _existing(paths):
    for item in paths:
        if not item:
            continue
        p = Path(item)
        if p.exists():
            return p
    return None


def _dsh_resources():
    local = os.environ.get("LOCALAPPDATA")
    return Path(local) / "Programs" / "DeepSeek Harness" / "resources" if local else None


_DSH = _dsh_resources()
NODE = _existing([
    os.environ.get("DSH_NODE"),
    shutil.which("node"),
    _DSH / "runtime" / "primary-runtime" / "dependencies" / "node" / "bin" / "node.exe" if _DSH else None,
])
CLI = _existing([
    os.environ.get("DSH_OFFICE_CLI"),
    _DSH / "app.asar.unpacked" / "dsh" / "node_modules" / "@deepseek-ai"
    / "libreoffice-kit" / "lib" / "cli.js" if _DSH else None,
])
BOOK_NAME = "业余无线电实用数学物理-书稿"
TITLE = "业余无线电实用数学物理"
SUBTITLE = "电台里的数学与物理"
DESCRIPTION = "写给想弄明白天线、馈线、传播与设备原理的短波爱好者"
EDITION = "本书编写组 · 2026 年 10 月 · 修订稿 v0.7"
HEADER = "业余无线电实用数学物理"
AUTHOR = "本书编写组"


def chapter_files(root: Path):
    return [
        p
        for p in sorted(root.glob("*.md"))
        if CHAPTER_RE.match(p.name) and not p.name.startswith("00-")
    ]


def convert(docx_path: Path, pdf_path: Path):
    if not CLI:
        raise RuntimeError(
            "未找到 LibreOffice Kit CLI。请设置环境变量 DSH_OFFICE_CLI 指向 cli.js，"
            "或安装 DeepSeek Harness 后重试。"
        )
    if pdf_path.exists():
        pdf_path.unlink()
    subprocess.run(
        [str(NODE), str(CLI), "convert",
         "--input", str(docx_path), "--output", str(pdf_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    root = Path(__file__).resolve().parent.parent
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)

    chapters = chapter_files(root)
    if not chapters:
        print("no chapters found")
        return 1
    print(f"chapters: {len(chapters)}")

    for md in chapters:
        out = build_dir / f"{md.stem}.docx"
        info = md2docx.build(
            md, out, "a5", asset_root=root,
            title_text=TITLE, subtitle_text=SUBTITLE,
            header_title=HEADER, header_author=AUTHOR,
        )
        print(f"OK {md.name} -> {out.name} "
              f"paragraphs={info['paragraphs']} tables={info['tables']}")

    combined = "\n\n".join(
        p.read_text(encoding="utf-8").strip() for p in chapters
    )
    combined_md = build_dir / "_书稿.md"
    combined_md.write_text(combined, encoding="utf-8")

    book = build_dir / f"{BOOK_NAME}.docx"
    book_pdf = build_dir / f"{BOOK_NAME}.pdf"
    toc_enabled = bool(NODE and CLI and NODE.exists() and CLI.exists())

    def build_book(entries=None):
        md2docx.build(
            combined_md, book, "a5", cover=True, chapter_breaks=True,
            toc_entries=entries, asset_root=root,
            title_text=TITLE, subtitle_text=SUBTITLE,
            description_text=DESCRIPTION, edition_text=EDITION,
            header_title=HEADER, header_author=AUTHOR,
        )

    entries = []
    if toc_enabled:
        try:
            build_book()
            convert(book, book_pdf)
            entries = extract(book_pdf)
            entries = [e for e in entries
                       if not re.fullmatch(r"[A-Z](\s*[–-]\s*[A-Z])?", e[1].strip())]
            print(f"outline: {len(entries)} entries (TOC, 附录E 字母条已过滤)")
            for _ in range(4):
                if not entries:
                    break
                build_book(entries)
                convert(book, book_pdf)
                shifted = extract(book_pdf)
                shifted = [e for e in shifted
                           if not re.fullmatch(r"[A-Z](\s*[–-]\s*[A-Z])?", e[1].strip())]
                if [(l, t, p) for l, t, p in shifted] == entries:
                    print("TOC page numbers stable")
                    break
                entries = shifted
        except Exception as exc:  # fall back to a book without TOC
            print(f"TOC build failed, falling back: {exc}")
            toc_enabled = False

    if not toc_enabled:
        build_book()
        convert(book, book_pdf)

    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(book_pdf)).pages)
        (build_dir / "_page_count.json").write_text(
            __import__("json").dumps({"pages": pages}), encoding="utf-8")
    except Exception:
        pages = "?"
    print(f"BOOK {book.name} -> {book_pdf.name} "
          f"(pages: {pages}, toc entries: {len(entries) if toc_enabled else 0})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
