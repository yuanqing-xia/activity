#!/usr/bin/env python3
"""
Universal Office Parser (docx, xlsx, pptx) using standard library.
Extracts plain text content from OpenXML files.
"""

import argparse
import sys
import zipfile
import re
from xml.etree import ElementTree

# XML Namespaces
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    's': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
}

def clean_xml_tag(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def parse_docx(zf):
    """Extract text from word/document.xml"""
    try:
        with zf.open('word/document.xml') as f:
            tree = ElementTree.parse(f)

        text_parts = []
        for elem in tree.iter():
            tag = clean_xml_tag(elem.tag)
            if tag == 't' and elem.text:
                text_parts.append(elem.text)
            elif tag == 'br' or tag == 'p':
                text_parts.append('\n')
            elif tag == 'tab':
                text_parts.append('\t')
        return "".join(text_parts)
    except KeyError:
        return "[Error: Invalid docx structure]"

def parse_pptx(zf):
    """Extract text from ppt/slides/slide*.xml"""
    text_parts = []

    # Find all slide files
    slides = [n for n in zf.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
    # Sort by slide number (approximate)
    slides.sort(key=lambda x: int(re.search(r'slide(\d+)\.xml', x).group(1) or 0))

    for slide in slides:
        text_parts.append(f"\n--- Slide {slide} ---\n")
        with zf.open(slide) as f:
            tree = ElementTree.parse(f)

        for elem in tree.iter():
            tag = clean_xml_tag(elem.tag)
            if tag == 't' and elem.text:
                text_parts.append(elem.text + " ")
        text_parts.append("\n")

    return "".join(text_parts)

def parse_xlsx(zf):
    """Extract text from sharedStrings and sheets"""
    text_parts = []

    # 1. Extract Shared Strings (common text dictionary)
    shared_strings = []
    try:
        with zf.open('xl/sharedStrings.xml') as f:
            tree = ElementTree.parse(f)
        for elem in tree.iter():
            tag = clean_xml_tag(elem.tag)
            if tag == 't' and elem.text:
                shared_strings.append(elem.text)
    except KeyError:
        pass # No shared strings

    # 2. Extract inline strings and numbers from sheets
    # Note: Reconstructing full table structure is complex without external libs.
    # We focus on extracting content for context.
    sheets = [n for n in zf.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
    sheets.sort()

    for sheet in sheets:
        text_parts.append(f"\n--- Sheet {sheet} ---\n")
        with zf.open(sheet) as f:
            tree = ElementTree.parse(f)

        for elem in tree.iter():
            tag = clean_xml_tag(elem.tag)
            # v = value, t = inline string text
            if tag == 'v' and elem.text:
                # If it's an index to sharedStrings, we might need logic to map it,
                # but simple extraction often misses mapping context. 
                # For simplicity in stdlib, we just dump values.
                # If value is an integer index, it might be meaningless without lookup.
                # Heuristic: if it looks like a number, keep it. 
                if elem.text.isdigit() and int(elem.text) < len(shared_strings):
                        # It *might* be an index if the cell type is 's' (sharedString)
                        # But accessing parent attributes here is tricky with iter().
                        # We'll stick to dumping shared_strings at the end or beginning.
                        pass
                else:
                    text_parts.append(elem.text + " ")
            elif tag == 't' and elem.text:
                text_parts.append(elem.text + " ")
        text_parts.append("\n")

    # Append shared strings at the end as a "Data Dictionary"
    if shared_strings:
        text_parts.append("\n--- Shared Text Data ---\n")
        text_parts.append(" ".join(shared_strings))

    return "".join(text_parts)

def main():
    parser = argparse.ArgumentParser(description="Extract text from Office files")
    parser.add_argument("path", help="Path to .docx, .xlsx, or .pptx file")
    args = parser.parse_args()

    path_lower = args.path.lower()

    try:
        if not zipfile.is_zipfile(args.path):
            print("Error: Not a valid zip/office file (might be binary format like .doc/.xls/.ppt)")
            return 1

        with zipfile.ZipFile(args.path, 'r') as zf:
            if path_lower.endswith('.docx'):
                print(parse_docx(zf))
            elif path_lower.endswith('.pptx'):
                print(parse_pptx(zf))
            elif path_lower.endswith('.xlsx'):
                print(parse_xlsx(zf))
            else:
                # Auto-detect based on contents
                names = zf.namelist()
                if 'word/document.xml' in names:
                    print(parse_docx(zf))
                elif 'xl/workbook.xml' in names:
                    print(parse_xlsx(zf))
                elif 'ppt/presentation.xml' in names:
                    print(parse_pptx(zf))
                else:
                    print("Error: Unknown Office XML format")
                    return 1

    except Exception as e:
        print(f"Error parsing file: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
