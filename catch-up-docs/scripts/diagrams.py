"""Deterministic, self-contained SVG primitives matching the reference guide."""
from __future__ import annotations
import html
import math
import re
import unicodedata
import xml.etree.ElementTree as ET

SVG_STYLE = """text{font-family:-apple-system,BlinkMacSystemFont,'Noto Sans JP','Hiragino Kaku Gothic ProN',Meiryo,sans-serif}.svg-title{font-size:14px;font-weight:650;fill:#213b4b}.svg-sub{font-size:10px;fill:#5d7184}.path-label{font:10px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#66778a}.layer-label{font:10px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#738696;letter-spacing:1px}"""

def esc(value):
    return html.escape(str(value), quote=True)

def ident(value):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", str(value)):
        raise ValueError(f"ID must be lowercase ASCII with hyphens: {value!r}")
    return value

def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("SVG coordinates must be finite")
    return f"{value:g}"

def text_width(value, size):
    return sum(0 if unicodedata.combining(c) else size * (1 if unicodedata.east_asian_width(c) in 'WF' else .57) for c in value)

def wrap(value, width, size=10):
    """Conservative line splitting; authors can specify explicit subtitle lines."""
    lines = []
    for raw in str(value).splitlines() or ['']:
        line = ''
        for char in raw:
            if line and text_width(line + char, size) > width:
                lines.append(line)
                line = ''
            line += char
        if line:
            lines.append(line)
    return lines

def label(x, y, value, cls='svg-title', anchor='start'):
    if cls not in ('svg-title', 'svg-sub', 'path-label', 'layer-label') or anchor not in ('start', 'middle', 'end'):
        raise ValueError('Unsupported SVG text style or anchor')
    return f'<text x="{number(x)}" y="{number(y)}" class="{cls}" text-anchor="{anchor}">{esc(value)}</text>'

def rect(item, width, height):
    x, y, w, h = [float(item[k]) for k in ('x', 'y', 'w', 'h')]
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise ValueError(f"SVG rectangle exceeds viewBox: {item}")
    return x, y, w, h

def node_geometry(item, width, height):
    item = dict(item)
    item.setdefault('h', 82)
    x, y, w, h = rect(item, width, height)
    if w < 120 or h < 65:
        raise ValueError(f"Node {item.get('id')} must be at least 120 × 65; use annotations for compact text")
    available = w - (75 if item.get('icon') else 34)
    if text_width(item['title'], 14) > available:
        raise ValueError(f"Node title {item['title']!r} is too wide; shorten it or increase w")
    raw_lines = item.get('subtitle', [])
    if isinstance(raw_lines, str):
        raw_lines = raw_lines.split('|')
    lines = [line for raw in raw_lines for line in wrap(raw, available)]
    if lines and 49 + (len(lines) - 1) * 16 > h - 12:
        raise ValueError(f"Node {item.get('id')} needs more height for {len(lines)} subtitle lines")
    return x, y, w, h, lines

def anchor(item, side):
    x, y, w, h = [float(item[k]) for k in ('x', 'y', 'w', 'h')]
    return {'left': (x, y+h/2), 'right': (x+w, y+h/2), 'top': (x+w/2, y), 'bottom': (x+w/2, y+h)}[side]

def edge_points(item, nodes):
    if 'points' in item:
        return item['points']
    start_side, end_side = item.get('from_side', 'right'), item.get('to_side', 'left')
    start, end = anchor(nodes[item['from']], start_side), anchor(nodes[item['to']], end_side)
    if 'via' in item:
        return [start, *item['via'], end]
    if start[0] == end[0] or start[1] == end[1]:
        return [start, end]
    if start_side in ('left', 'right') and end_side in ('left', 'right'):
        mid = (start[0] + end[0]) / 2
        return [start, (mid, start[1]), (mid, end[1]), end]
    if start_side in ('top', 'bottom') and end_side in ('top', 'bottom'):
        mid = (start[1] + end[1]) / 2
        return [start, (start[0], mid), (end[0], mid), end]
    return [start, (end[0], start[1]), end]

def render_diagram(spec, icon_uri):
    diagram_id = ident(spec['id'])
    width, height = float(spec.get('width', 900)), float(spec['height'])
    if width <= 0 or height <= 0:
        raise ValueError('SVG dimensions must be positive')
    marker = diagram_id + '-arrow'
    title_id = diagram_id + '-title'
    desc_id = diagram_id + '-desc'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {number(width)} {number(height)}" role="img" aria-labelledby="{title_id} {desc_id}">',
           f'<title id="{title_id}">{esc(spec["title"])}</title>',
           f'<desc id="{desc_id}">{esc(spec.get("description", spec.get("caption", "")))}</desc>',
           f'<style>{SVG_STYLE}</style>',
           f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="#729597"/></marker></defs>']
    for band in spec.get('bands', []):
        x, y, w, h = rect(band, width, height)
        out.append(f'<rect x="{number(x)}" y="{number(y)}" width="{number(w)}" height="{number(h)}" rx="10" fill="#f5f9fa" stroke="#e2e9ed" stroke-dasharray="5 4"/>')
        out.append(label(x+15, y+22, band['label'], 'layer-label'))
    nodes = {}
    geometries = {}
    for node in spec.get('nodes', []):
        node = dict(node)
        node.setdefault('h', 82)
        node_id = ident(node['id'])
        if node_id in nodes:
            raise ValueError(f'Duplicate node ID: {node_id}')
        geometry = node_geometry(node, width, height)
        for other_id, other in geometries.items():
            x, y, w, h = geometry[:4]
            ox, oy, ow, oh = other[:4]
            if x < ox+ow and x+w > ox and y < oy+oh and y+h > oy:
                raise ValueError(f'Nodes overlap: {node_id} and {other_id}')
        nodes[node_id] = node
        geometries[node_id] = geometry
    labels = []
    for edge in spec.get('edges', []):
        points = edge_points(edge, nodes)
        if len(points) < 2:
            raise ValueError('Each edge needs at least two points')
        for x, y in points:
            if not 0 <= float(x) <= width or not 0 <= float(y) <= height:
                raise ValueError(f'Edge exceeds viewBox: {points}')
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            if x1 != x2 and y1 != y2:
                raise ValueError('Use orthogonal edge segments; add via points for this route')
        d = 'M' + ' L'.join(f'{number(x)} {number(y)}' for x, y in points)
        out.append(f'<path d="{d}" fill="none" stroke="#729597" stroke-width="1.5" marker-end="url(#{marker})"/>')
        if edge.get('label'):
            if 'label_at' not in edge:
                raise ValueError('Labeled edges need label_at: [x, y]')
            labels.append(label(*edge['label_at'], edge['label'], 'path-label'))
    for key, node in nodes.items():
        x, y, w, h, lines = geometries[key]
        out.append(f'<rect x="{number(x)}" y="{number(y)}" width="{number(w)}" height="{number(h)}" rx="8" fill="#fff" stroke="#d6e1e8"/>')
        tx = x+17
        if node.get('icon'):
            out.append(f'<image href="{esc(icon_uri(node["icon"]))}" x="{number(x+15)}" y="{number(y+17)}" width="31" height="31"/>')
            tx = x+58
        out.append(label(tx, y+30, node['title']))
        for i, line in enumerate(lines):
            out.append(label(tx, y+49+i*16, line, 'svg-sub'))
    out.extend(labels)
    for item in spec.get('annotations', []):
        out.append(label(item['x'], item['y'], item['text'], item.get('class', 'svg-sub')))
    out.append('</svg>')
    svg = ''.join(out)
    ET.fromstring(svg)
    return svg
