#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the PDF outline (bookmarks) as (level, title, page).

Minimal parser for LibreOffice-exported PDFs without object streams.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OBJ_RE = re.compile(rb"(\d+)\s+0\s+obj(.*?)endobj", re.S)
REF_RE = re.compile(rb"(\d+)\s+0\s+R")
TITLE_HEX_RE = re.compile(rb"/Title\s*<([0-9A-Fa-f]+)>")
TITLE_LIT_RE = re.compile(rb"/Title\s*\((.*?)\)", re.S)


def parse_objects(data: bytes):
    objects = {}
    for match in OBJ_RE.finditer(data):
        objects[int(match.group(1))] = match.group(2)
    return objects


def ref_of(body: bytes, key: bytes):
    idx = body.find(key)
    if idx < 0:
        return None
    m = REF_RE.search(body, idx)
    return int(m.group(1)) if m else None


def page_order(objects):
    catalog = None
    for oid, body in objects.items():
        if b"/Type/Catalog" in body or b"/Type /Catalog" in body:
            catalog = body
            break
    if catalog is None:
        return []
    pages_root = ref_of(catalog, b"/Pages")
    order = []

    def walk(oid):
        body = objects.get(oid, b"")
        kids_idx = body.find(b"/Kids")
        if kids_idx >= 0:
            start = body.find(b"[", kids_idx)
            end = body.find(b"]", start)
            for m in REF_RE.finditer(body[start:end]):
                walk(int(m.group(1)))
        elif b"/Type/Page" in body or b"/Type /Page" in body:
            order.append(oid)

    walk(pages_root)
    return order


def decode_title(body: bytes):
    m = TITLE_HEX_RE.search(body)
    if m:
        hexstr = m.group(1).decode("ascii")
        raw = bytes.fromhex(hexstr)
        try:
            return raw.decode("utf-16-be").lstrip("\ufeff")
        except UnicodeDecodeError:
            return raw.decode("latin-1")
    m = TITLE_LIT_RE.search(body)
    if m:
        raw = m.group(1)
        raw = raw.replace(rb"\(", b"(").replace(rb"\)", b")")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")
    return ""


def dest_page(body: bytes, page_index):
    idx = body.find(b"/Dest")
    if idx < 0:
        idx = body.find(b"/A")
        if idx < 0:
            return None
    m = REF_RE.search(body, idx)
    if not m:
        return None
    return page_index.get(int(m.group(1)))


def extract(path: Path):
    data = path.read_bytes()
    objects = parse_objects(data)
    order = page_order(objects)
    page_index = {oid: i + 1 for i, oid in enumerate(order)}

    catalog = next(
        (body for body in objects.values()
         if b"/Type/Catalog" in body or b"/Type /Catalog" in body),
        None,
    )
    root_oid = ref_of(catalog, b"/Outlines") if catalog else None
    root = objects.get(root_oid) if root_oid else None
    entries = []
    if root is None:
        return entries

    def traverse(first_oid, level):
        oid = first_oid
        while oid:
            body = objects.get(oid, b"")
            title = decode_title(body)
            page = dest_page(body, page_index)
            entries.append((level, title, page))
            child = ref_of(body, b"/First")
            if child:
                traverse(child, level + 1)
            oid = ref_of(body, b"/Next")

    first = ref_of(root, b"/First")
    if first:
        traverse(first, 1)
    return entries


def main():
    entries = extract(Path(sys.argv[1]))
    print("entries:", len(entries))
    for level, title, page in entries:
        print(f"{'  ' * (level - 1)}{title}  ...  {page}")


if __name__ == "__main__":
    main()
