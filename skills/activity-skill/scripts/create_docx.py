#!/usr/bin/env python3
"""Small zero-dependency .docx generator and template filler.

Modes:
  Create new:
    python3 create_docx.py out.docx --title "Title" "Body paragraph"
    python3 create_docx.py out.docx --title "Title" --content-file content.md

  Fill template:
    python3 create_docx.py out.docx --template template.docx --replace "{{name}}::Project"

Template replacement preserves the original .docx package and edits Word XML
parts in place. It reports missing placeholders instead of silently succeeding.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="240"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:before="180" w:after="100"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
  </w:style>
</w:styles>
"""


@dataclass(frozen=True)
class ReplacementResult:
    output_path: Path
    replaced: List[str]
    missing: List[str]
    touched_parts: List[str]


def xml_text(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def paragraph_xml(text: str, style: Optional[str] = None) -> str:
    text = text.rstrip()
    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{properties}<w:r><w:t>{xml_text(text)}</w:t></w:r></w:p>"


def document_xml(lines: Sequence[str]) -> str:
    body: List[str] = []
    plain_index = 0
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            body.append("<w:p/>")
            continue
        if line.startswith("# "):
            body.append(paragraph_xml(line[2:].strip(), "Heading1"))
        elif line.startswith("## "):
            body.append(paragraph_xml(line[3:].strip(), "Heading2"))
        elif plain_index == 0:
            body.append(paragraph_xml(line, "Title"))
        else:
            body.append(paragraph_xml(line))
        plain_index += 1

    section = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}{section}</w:body></w:document>"
    )


def create_new_docx(output_path: Path, lines: Sequence[str]) -> None:
    if not lines:
        raise ValueError("No content provided. Pass text arguments or --content-file.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/document.xml", document_xml(lines))
        zf.writestr("word/styles.xml", STYLES_XML)


def parse_replacements(items: Optional[Iterable[str]]) -> List[Tuple[str, str]]:
    replacements: List[Tuple[str, str]] = []
    for item in items or []:
        if "::" not in item:
            raise ValueError(f"Invalid --replace value {item!r}; expected OLD::NEW")
        old, new = item.split("::", 1)
        if not old:
            raise ValueError("--replace OLD value cannot be empty")
        replacements.append((old, new))
    return replacements


def is_word_xml_part(name: str) -> bool:
    if name == "word/document.xml":
        return True
    basename = os.path.basename(name)
    return name.startswith("word/") and (
        basename.startswith("header") or basename.startswith("footer")
    ) and name.endswith(".xml")


def fill_template_docx(
    template_path: Path,
    output_path: Path,
    replacements: Sequence[Tuple[str, str]],
    allow_missing: bool = False,
) -> ReplacementResult:
    if not zipfile.is_zipfile(template_path):
        raise ValueError(f"Template is not a valid .docx file: {template_path}")
    if not replacements:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_path, output_path)
        return ReplacementResult(output_path, [], [], [])

    seen = {old: False for old, _ in replacements}
    touched_parts: List[str] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(template_path, "r") as zin, zipfile.ZipFile(
        output_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        names = zin.namelist()
        if "word/document.xml" not in names:
            raise ValueError("Template does not contain word/document.xml")

        for info in zin.infolist():
            data = zin.read(info.filename)
            if is_word_xml_part(info.filename):
                text = data.decode("utf-8")
                original = text
                for old, new in replacements:
                    if old in text:
                        seen[old] = True
                        text = text.replace(old, xml_text(new))
                if text != original:
                    touched_parts.append(info.filename)
                data = text.encode("utf-8")
            zout.writestr(info, data)

    missing = [old for old, found in seen.items() if not found]
    if missing and not allow_missing:
        output_path.unlink(missing_ok=True)
        joined = ", ".join(repr(item) for item in missing)
        raise ValueError(f"Placeholder(s) not found in template: {joined}")

    replaced = [old for old, found in seen.items() if found]
    return ReplacementResult(output_path, replaced, missing, touched_parts)


def read_content_file(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def collect_lines(args: argparse.Namespace) -> List[str]:
    lines: List[str] = []
    if args.title:
        lines.append(args.title)
    if args.content_file:
        lines.extend(read_content_file(Path(args.content_file)))
    lines.extend(args.content)
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a simple .docx file or fill placeholders in a .docx template.",
        epilog="Any extra arguments are treated as new-document paragraphs.",
    )
    parser.add_argument("output", help="Output .docx filename")
    parser.add_argument("--title", help="Title for new-document mode")
    parser.add_argument("--content-file", help="UTF-8 text/Markdown file for new-document mode")
    parser.add_argument("--template", help="Template .docx path for template-fill mode")
    parser.add_argument(
        "--replace",
        action="append",
        help='Template replacement in "OLD::NEW" format. Repeat for multiple fields.',
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Do not fail when a --replace placeholder is not found; report it instead.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args, extra_content = parser.parse_known_args(argv)
    for item in extra_content:
        if item.startswith("--"):
            parser.error(f"unrecognized option: {item}")
    args.content = extra_content
    output_path = Path(args.output)

    try:
        if args.template:
            if args.content:
                parser.error("Template mode does not accept extra content arguments")
            result = fill_template_docx(
                Path(args.template),
                output_path,
                parse_replacements(args.replace),
                allow_missing=args.allow_missing,
            )
            print(f"Created {result.output_path}")
            if result.touched_parts:
                print("Updated parts: " + ", ".join(result.touched_parts))
            if result.replaced:
                print("Replaced: " + ", ".join(result.replaced))
            if result.missing:
                print("Missing: " + ", ".join(result.missing), file=sys.stderr)
        else:
            if args.replace or args.allow_missing:
                parser.error("--replace/--allow-missing require --template")
            create_new_docx(output_path, collect_lines(args))
            print(f"Created {output_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
