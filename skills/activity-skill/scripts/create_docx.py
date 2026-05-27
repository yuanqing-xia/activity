#!/usr/bin/env python3
    """
    Zero-dependency .docx generator & template filler.

    Modes:
    1. Create new: python create_docx.py out.docx "Title" "Body..."
    2. Fill template: python create_docx.py out.docx --template input.docx --replace "OLD_TEXT::NEW_TEXT" "Old Title::New Title"
    """

    import sys
    import zipfile
    import os
    import shutil
    import tempfile
    import argparse
    from typing import List, Tuple

    # --- Mode 1: Create New (Simple XML) ---

    CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
        <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
        <Default Extension="xml" ContentType="application/xml"/>
        <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    </Types>"""

    RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    </Relationships>"""

    DOC_HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>"""

    DOC_FOOTER = """</w:body></w:document>"""

    def create_paragraph(text: str, style: str = None) -> str:
        xml = ['<w:p>']
        if style:
            xml.append(f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>')
        xml.append('<w:r><w:t>')
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml.append(safe_text)
        xml.append('</w:t></w:r>')
        xml.append('</w:p>')
        return "".join(xml)

    def create_new_docx(filename: str, content_lines: List[str]):
        body_parts = []
        for i, line in enumerate(content_lines):
            line = line.strip()
            if not line: continue
            if i == 0 and not line.startswith('#'):
                body_parts.append(create_paragraph(line, "Title"))
            elif line.startswith('# '):
                body_parts.append(create_paragraph(line[2:], "Heading1"))
            elif line.startswith('## '):
                body_parts.append(create_paragraph(line[3:], "Heading2"))
            else:
                body_parts.append(create_paragraph(line))

        full_doc_xml = DOC_HEADER + "".join(body_parts) + DOC_FOOTER
        try:
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('[Content_Types].xml', CONTENT_TYPES)
                zf.writestr('_rels/.rels', RELS)
                zf.writestr('word/document.xml', full_doc_xml)
            return True
        except Exception as e:
            sys.stderr.write(f"Error creating docx: {e}
")
            return False

    # --- Mode 2: Fill Template (Preserve Styles) ---

    def fill_template_docx(template_path: str, output_path: str, replacements: List[Tuple[str, str]]):
        """
        Unzip template, replace text in document.xml, re-zip.
        NOTE: This is a simple string replacement. If XML tags split the search string, it won't match.
        """
        try:
            temp_dir = tempfile.mkdtemp()

            # 1. Extract all
            with zipfile.ZipFile(template_path, 'r') as zin:
                zin.extractall(temp_dir)

            # 2. Read and Replace in word/document.xml
            doc_xml_path = os.path.join(temp_dir, 'word/document.xml')
            if os.path.exists(doc_xml_path):
                with open(doc_xml_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for old, new in replacements:
                    # XML escape for new content
                    new_safe = new.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    content = content.replace(old, new_safe)

                with open(doc_xml_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                sys.stderr.write("Error: word/document.xml not found in template.
")
                return False

            # 3. Zip back to output
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zout.write(full_path, rel_path)

            shutil.rmtree(temp_dir)
            return True

        except Exception as e:
            sys.stderr.write(f"Template error: {e}
")
            return False

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("output", help="Output .docx filename")
        parser.add_argument("content", nargs="*", help="Content lines (for new doc)")
        parser.add_argument("--template", help="Path to template .docx")
        parser.add_argument("--replace", action="append", help="Format: 'OLD::NEW'")

        # If piping input
        if not sys.stdin.isatty():
             # Read stdin if available
             piped = sys.stdin.read().splitlines()
             if piped:
                 sys.argv.extend(piped)

        args = parser.parse_args()

        if args.template:
            # If no replacements provided, just copy the template to output
            if not args.replace:
                try:
                    shutil.copy2(args.template, args.output)
                    print(f"Created {args.output} from template (no replacements)")
                    return 0
                except Exception as e:
                    print(f"Error copying template: {e}")
                    return 1
            
            replacements = []
            for item in args.replace:
                if "::" in item:
                    parts = item.split("::", 1)
                    replacements.append((parts[0], parts[1]))

            if fill_template_docx(args.template, args.output, replacements):
                print(f"Created {args.output} from template")
            else:
                return 1
        else:
            if create_new_docx(args.output, args.content):
                print(f"Created {args.output}")
            else:
                return 1
        return 0

    if __name__ == "__main__":
        sys.exit(main())
