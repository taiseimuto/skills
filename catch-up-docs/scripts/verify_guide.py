#!/usr/bin/env python3
"""Verify artifact links, IDs, SVG resources, and single-file independence offline."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.anchors, self.resources, self.errors = [], [], [], []
        self.h1 = self.chapters = self.techs = self.diagrams = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        classes = a.get('class', '').split()
        if tag == 'h1': self.h1 += 1
        if tag == 'section' and 'chapter' in classes: self.chapters += 1
        if tag == 'details' and 'tech' in classes:
            self.techs += 1
            if 'open' in a: self.errors.append('Technology details must initially be closed')
        if tag == 'figure' and 'diagram' in classes: self.diagrams += 1
        if tag == 'a' and a.get('href', '').startswith('#'): self.anchors.append(a['href'][1:])
        for key in ('src', 'poster'):
            if a.get(key): self.resources.append(a[key])
        if tag == 'image' and a.get('href'): self.resources.append(a['href'])
        if tag == 'link' and a.get('rel') in ('stylesheet', 'icon') and a.get('href'): self.resources.append(a['href'])
        if tag in ('iframe', 'object', 'embed'): self.errors.append(f'Unexpected runtime embedding: {tag}')
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)

def verify(path, single=False):
    content = path.read_text(encoding='utf-8')
    p = Inspect(); p.feed(content)
    errors = list(p.errors)
    errors += [f'Duplicate ID: {key}' for key, count in Counter(p.ids).items() if count > 1]
    errors += [f'Missing anchor: {key}' for key in p.anchors if key not in p.ids]
    if p.h1 != 1: errors.append(f'Expected one h1, found {p.h1}')
    if p.chapters == 0: errors.append('No chapters')
    for source in p.resources:
        if source.startswith(('data:', '#')): continue
        if source.startswith('//') or urlparse(source).scheme:
            errors.append(f'External runtime resource: {source}')
        elif single: errors.append(f'Single HTML depends on another file: {source}')
        elif not (path.parent/unquote(source.split('#')[0].split('?')[0])).is_file():
            errors.append(f'Missing local resource: {source}')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', content, re.S))
    if not single and (path.parent/'style.css').exists(): css += (path.parent/'style.css').read_text()
    if re.search(r'@import|url\(\s*[\'"]?(?:https?:)?//', css, re.I): errors.append('CSS imports a remote resource')
    diagrams = path.parent/'diagrams'
    if not single and diagrams.is_dir():
        for file in diagrams.glob('*.svg'):
            try:
                tree = ET.fromstring(file.read_text())
                for node in tree.iter():
                    for key, value in node.attrib.items():
                        if key.split('}')[-1] == 'href' and not value.startswith(('data:', '#')):
                            errors.append(f'Exported SVG has external reference: {file.name}: {value}')
            except ET.ParseError as exc: errors.append(f'Invalid SVG {file.name}: {exc}')
    return {'path':str(path), 'single':single, 'chapters':p.chapters, 'tech_notes':p.techs, 'diagrams':p.diagrams, 'errors':errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html', type=Path)
    parser.add_argument('--single', action='store_true')
    args = parser.parse_args()
    result = verify(args.html.resolve(), args.single)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))
if __name__ == '__main__': main()
