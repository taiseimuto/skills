#!/usr/bin/env python3
"""Check a portable README SVG. Python 3 standard library only; no rendering."""

import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
URL_RE = re.compile(r"url\(\s*([^)]*?)\s*\)", re.IGNORECASE)


def local_name(name):
    return name.rsplit("}", 1)[-1]


def check_svg(path):
    """Return structural errors; this is not a security or visual audit."""
    try:
        source = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [f"Cannot read SVG: {exc}"]
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.IGNORECASE):
        return ["DOCTYPE/entity declarations are not supported in portable diagrams."]
    if "<?xml-stylesheet" in source.lower():
        return ["External XML stylesheet processing instructions are not supported."]
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        return [f"Invalid XML: {exc}"]
    errors = []
    if root.tag != f"{{{SVG_NS}}}svg":
        errors.append("Root must be svg in the SVG namespace.")
    box = root.get("viewBox", "").replace(",", " ").split()
    try:
        numbers = [float(part) for part in box]
        if len(numbers) != 4 or numbers[2] <= 0 or numbers[3] <= 0:
            raise ValueError
    except ValueError:
        errors.append("Provide a viewBox with four numbers and positive width/height.")
    if root.get("role") != "img":
        errors.append('Root must have role="img".')

    ids = {}
    refs = []
    for element in root.iter():
        tag = local_name(element.tag)
        ident = element.get("id")
        if ident:
            if ident in ids:
                errors.append(f"Duplicate id: {ident}")
            ids[ident] = element
        if tag in {"script", "foreignObject", "iframe", "animate", "animateTransform", "set"}:
            errors.append(f"Unsupported active or nonportable element: {tag}")
        for attribute, value in element.attrib.items():
            name = local_name(attribute)
            if name.lower().startswith("on"):
                errors.append(f"Event handler is not supported: {name}")
            if name == "href":
                if value.startswith("#") and len(value) > 1:
                    refs.append(value[1:])
                else:
                    errors.append(f"Nonlocal href; embed the vector instead: {value[:100]}")
            # Also catches nested svg src/base attributes, without treating namespaces as URLs.
            if name.lower() in {"src", "base"}:
                errors.append(f"Nonportable resource attribute: {name}")
            check_css_urls(value, refs, errors)
        if tag == "style":
            css = "".join(element.itertext())
            # Comments are not resource requests.
            css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
            if re.search(r"@(?:import|font-face)\b", css, re.IGNORECASE):
                errors.append("External CSS imports/custom font faces are not supported.")
            check_css_urls(css, refs, errors)

    labelled = root.get("aria-labelledby", "").split()
    for required in ("title", "desc"):
        if not any(
            ident in ids
            and local_name(ids[ident].tag) == required
            and "".join(ids[ident].itertext()).strip()
            for ident in labelled
        ):
            errors.append(f"aria-labelledby must reference a nonempty {required} element.")
    for ident in set(refs + labelled):
        if ident not in ids:
            errors.append(f"Unresolved internal reference: #{ident}")
    return errors


def check_css_urls(value, refs, errors):
    for match in URL_RE.finditer(value):
        target = match.group(1).strip().strip("\"'")
        if target.startswith("#") and len(target) > 1:
            refs.append(target[1:])
        else:
            errors.append(f"Nonlocal CSS URL; embed the resource: {target[:100]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.files:
        errors = check_svg(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK {path} (structure only; render and inspect separately)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
