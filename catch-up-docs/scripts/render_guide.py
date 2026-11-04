#!/usr/bin/env python3
"""Render repository catch-up guides. Python 3.10+, standard library only."""
from __future__ import annotations
import argparse
import base64
import html
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
from diagrams import ident, render_diagram

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets/template'

def esc(value):
    return html.escape(str(value), quote=True)

def safe_url(value):
    value = str(value)
    parsed = urlparse(value)
    if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f'Expected HTTP(S) URL without embedded credentials: {value!r}')
    return value

def external(url, title):
    return f'<a href="{esc(safe_url(url))}" target="_blank" rel="noopener noreferrer">{esc(title)} ↗</a>'

class Fragment(HTMLParser):
    """Allow authored prose markup, never active content or runtime resources."""
    tags = {'p', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'code', 'br', 'a', 'span', 'small'}
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.stack = []
    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            raise ValueError(f'Unsupported prose tag <{tag}>; use a structured content block')
        attr = dict(attrs)
        if any(k not in ('href', 'class', 'title') for k in attr):
            raise ValueError(f'Unsupported prose attributes: {attrs}')
        built = ''
        for key, val in attrs:
            if val is None:
                raise ValueError(f'Attribute {key} needs a value')
            if key == 'href':
                if not val.startswith('#'):
                    safe_url(val)
                    built += ' target="_blank" rel="noopener noreferrer"'
            if key == 'class' and val not in ('small', 'tag'):
                raise ValueError('Prose class must be small or tag; preserve the shared design')
            built += f' {key}="{esc(val)}"'
        self.parts.append(f'<{tag}{built}>')
        if tag != 'br': self.stack.append(tag)
    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError(f'Unbalanced prose closing tag: {tag}')
        self.parts.append(f'</{tag}>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != 'br': self.handle_endtag(tag)
    def handle_data(self, data): self.parts.append(esc(data))
    def handle_entityref(self, name): self.parts.append(esc(html.unescape('&' + name + ';')))
    def handle_charref(self, name): self.parts.append(esc(html.unescape('&#' + name + ';')))
    def handle_comment(self, data): pass

def prose(value):
    parser = Fragment()
    parser.feed(str(value))
    parser.close()
    if parser.stack: raise ValueError(f'Unclosed prose tags: {parser.stack}')
    return ''.join(parser.parts)

def data_script(value):
    text = json.dumps(value, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return '<script type="application/json" class="widget-data">' + text + '</script>'

class Renderer:
    def __init__(self, spec, base, single):
        self.spec, self.meta, self.base, self.single = spec, spec['meta'], base, single
        self.ids = set()
        self.diagrams = {}
        self.used_icons = {}
        self.tech_count = 0
        self.icons = {p.stem: p for p in (ROOT/'assets/icons').iterdir() if p.suffix in ('.svg', '.png', '.jpg', '.webp')}
        for key, value in self.meta.get('icons', {}).items():
            ident(key)
            path = (base/value).resolve()
            if not path.is_relative_to(base): raise ValueError('Custom icons must be inside the guide input directory')
            self.icons[key] = path
        self.repo = self.meta.get('repo_url')
        if self.repo:
            safe_url(self.repo)
            self.repo = self.repo.rstrip('/').removesuffix('.git')
        self.commit = self.meta.get('commit')
        if self.commit and not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', self.commit):
            raise ValueError('commit must be a full Git SHA, or null for an explicitly illustrative example')
    def claim(self, value):
        ident(value)
        if value in self.ids: raise ValueError(f'Duplicate document ID: {value}')
        self.ids.add(value)
        return value
    def icon(self, key, inline=False):
        ident(key)
        if key not in self.icons: raise ValueError(f'Unknown icon {key!r}; add a local meta.icons entry or omit icon')
        path = self.icons[key]
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in ('image/svg+xml', 'image/png', 'image/jpeg', 'image/webp', 'image/gif'):
            raise ValueError(f'Unsupported icon image: {path}')
        content = path.read_bytes()
        if mime == 'image/svg+xml':
            tree = ET.fromstring(content)
            for node in tree.iter():
                if node.tag.split('}')[-1] in ('script', 'foreignObject'):
                    raise ValueError('SVG icons must not contain active content')
                if any(k.lower().startswith('on') or (k.split('}')[-1] == 'href' and not v.startswith(('data:', '#'))) for k, v in node.attrib.items()):
                    raise ValueError('SVG icons must be self-contained without external references or handlers')
            if re.search(rb'(?:url\s*\(\s*[\'"]?https?://|@import)', content, re.I):
                raise ValueError('SVG icons must not load external CSS')
        self.used_icons[key] = path
        if self.single or inline: return f'data:{mime};base64,' + base64.b64encode(content).decode()
        return f'assets/icons/{key}{path.suffix.lower()}'
    def source_url(self, item):
        if 'url' in item: return safe_url(item['url'])
        if not self.repo or not self.commit: return None
        if not self.repo.startswith('https://github.com/'):
            raise ValueError('Auto source links currently support GitHub; provide explicit url for other hosts')
        path = item['path']
        if path.startswith('/') or '..' in Path(path).parts: raise ValueError('Source paths must be repository-relative')
        url = self.repo.rstrip('/') + '/blob/' + self.commit + '/' + quote(path, safe='/')
        if item.get('line'): url += '#L' + str(int(item['line']))
        return url
    def sources(self, items):
        links = []
        for item in items:
            if isinstance(item, str): item = {'path': item}
            title = item.get('label', item.get('path', item.get('url', 'source')))
            url = self.source_url(item)
            links.append(external(url, title) if url else '<code>' + esc(title) + '</code>')
        return '<div class="source">SOURCE / ' + ' '.join(links) + '</div>' if links else ''
    def blocks(self, items): return ''.join(self.block(item) for item in items)
    def block(self, b):
        kind = b['type']
        if kind == 'html': return prose(b['html'])
        if kind == 'code': return '<div class="code-wrap"><pre><code>' + esc(b['text'].strip()) + '</code></pre></div>'
        if kind == 'note':
            cls = ' warn' if b.get('kind') == 'warn' else ''
            return f'<aside class="note{cls}"><strong>{esc(b["title"])}</strong><div>{prose(b["html"])}</div></aside>'
        if kind == 'sources': return self.sources(b['items'])
        if kind == 'table':
            headers = b['headers']
            if any(len(row) != len(headers) for row in b['rows']): raise ValueError('Table rows must match header count')
            return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>'+esc(x)+'</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>'+prose(cell)+'</td>' for cell in row) + '</tr>' for row in b['rows']) + '</tbody></table></div>'
        if kind == 'columns':
            return '<div class="grid2">' + ''.join('<div class="panel">' + ('<div class="num">'+esc(c['eyebrow'])+'</div>' if c.get('eyebrow') else '') + '<h3>'+esc(c['title'])+'</h3>'+prose(c['html'])+'</div>' for c in b['items']) + '</div>'
        if kind == 'diagram':
            key = self.claim(b['id'])
            svg = render_diagram(b, lambda key: self.icon(key, inline=True))
            self.diagrams[key] = svg
            title = esc(b.get('figure_label', b['title']))
            return f'<figure class="diagram" id="{key}"><div class="diagram-toolbar"><span>{title}</span><button type="button" data-zoom="{key}">拡大 ↗</button></div><div class="diagram-scroll">{svg}</div><figcaption>{esc(b.get("caption", ""))} スマホは横スクロール・拡大できます。</figcaption></figure>' + self.sources(b.get('sources', []))
        if kind == 'tabs':
            key = self.claim(b['id'])
            buttons, panels = [], []
            for i, item in enumerate(b['items']):
                panel_id = self.claim(f'{key}-panel-{i}')
                buttons.append(f'<button type="button" aria-pressed="{str(i==0).lower()}" aria-controls="{panel_id}" data-panel="{panel_id}">{esc(item["label"])}</button>')
                panels.append(f'<div id="{panel_id}" data-tab-panel {"hidden" if i else ""}>{self.blocks(item["blocks"])}</div>')
            return f'<div data-tabs id="{key}"><div class="tabs">' + ''.join(buttons) + '</div>' + ''.join(panels) + '</div>'
        if kind == 'tech_stack':
            key = self.claim(b['id'])
            search_id = self.claim(key + '-search')
            count = len(b['items']); self.tech_count += count
            groups = {}
            for tech in b['items']: groups.setdefault(tech.get('group', 'TECHNOLOGY'), []).append(tech)
            body = ''.join('<div class="tech-group"><div class="tech-group-title">'+esc(group)+'</div>'+''.join(self.tech(t) for t in items)+'</div>' for group, items in groups.items())
            return f'<div class="tech-widget" id="{key}"><div class="stack-toolbar"><input type="search" id="{search_id}" placeholder="技術を検索：ルーティング / 認証…" aria-label="技術解説を検索"><button type="button" data-expand>表示中をすべて開く</button><button type="button" data-collapse>すべて閉じる</button></div><p class="small tech-count" aria-live="polite">{count} 技術・ツール</p>{body}<p class="empty tech-empty" hidden>一致する技術はありません。別の語で検索してください。</p></div>'
        if kind == 'file_finder':
            key = self.claim(b['id']); select_id = self.claim(key+'-select')
            items = []
            for item in b['items']:
                item = dict(item)
                item['source_url'] = self.source_url({'path': item['file']})
                items.append(item)
            if not items: raise ValueError('file_finder needs at least one entry')
            options = ''.join(f'<option value="{i}">{esc(x["label"])}</option>' for i, x in enumerate(items))
            return f'<div class="finder" id="{key}"><label for="{select_id}">{esc(b.get("title", "どの画面を直したい？"))}</label><select id="{select_id}">{options}</select><div class="finder-result" aria-live="polite"></div>{data_script({"items":items})}</div>'
        if kind == 'checklist':
            key = self.claim(b['id']); items = []
            for i, item in enumerate(b['items']):
                if isinstance(item, str): item = {'id': f'item-{i}', 'label': item}
                check_id = self.claim(key+'-'+ident(item['id']))
                items.append(f'<li><label><input type="checkbox" id="{check_id}"><span>{esc(item["label"])}</span></label></li>')
            return f'<div class="check-widget" id="{key}"><h3>{esc(b.get("title", "到達チェック"))} <span class="complete-count"></span></h3><p class="small">チェックはこのブラウザ内にだけ保存。別端末とは同期しません。</p><ul class="checklist">'+''.join(items)+'</ul><button type="button" data-reset>チェックをリセット</button></div>'
        if kind == 'quiz':
            key = self.claim(b['id'])
            if not isinstance(b['correct'], int) or not 0 <= b['correct'] < len(b['answers']): raise ValueError('Quiz correct must be a zero-based answer index')
            answers = ''.join(f'<button type="button" data-answer="{i}" aria-pressed="false">{esc(answer)}</button>' for i, answer in enumerate(b['answers']))
            return f'<div class="quiz" id="{key}"><p>{esc(b["question"])}</p>{answers}<div class="feedback" role="status" hidden></div>{data_script({"correct":b["correct"], "explanation":b["explanation"]})}</div>'
        raise ValueError(f'Unknown block type: {kind}')
    def tech(self, t):
        icon = f'<img src="{esc(self.icon(t["icon"]))}" alt="" class="tech-icon" width="31" height="31" loading="lazy">' if t.get('icon') else '<span class="letter-icon">'+esc(t.get('monogram', t['name'][:2]))+'</span>'
        version = '<span class="version">'+esc(t['version'])+'</span>' if t.get('version') else ''
        where = self.sources(t.get('locations', []))
        motivation = '採用動機の記録' if t.get('motivation_status') == 'documented' else '採用動機の解釈'
        if t.get('motivation_status') == 'documented' and not t.get('motivation_sources'):
            raise ValueError('Documented motivation needs motivation_sources')
        definitions = '<dl><dt>どんな技術か</dt><dd>'+esc(t['what'])+'</dd><dt>このrepoの場所</dt><dd>'+where+'</dd><dt>'+motivation+'</dt><dd>'+esc(t['motivation'])+self.sources(t.get('motivation_sources', []))+'</dd></dl>'
        tradeoffs = '<div class="trade"><div><b>BENEFITS</b>'+esc(t['benefits'])+'</div><div><b>TRADE-OFFS</b>'+esc(t['tradeoffs'])+'</div></div>'
        attention = self.block({'type':'note', 'title':'このコードを読むとき', 'html':esc(t['attention'])}) if t.get('attention') else ''
        return '<details class="tech"><summary>'+icon+'<span class="summary-copy"><strong>'+esc(t['name'])+'</strong><small>'+esc(t['summary'])+'</small></span>'+version+'</summary><div class="detail-body">'+definitions+tradeoffs+attention+self.sources(t.get('docs', []))+'</div></details>'
    def page(self):
        chapters, nav = [], []
        sections = self.spec['chapters']
        if not sections: raise ValueError('A guide needs at least one chapter')
        for fixed in ['main', 'progress', 'guide-toc', 'close-nav', 'overlay', 'menu', 'diagram-modal', 'modal-title', 'modal-content', 'close-diagram', 'toast']: self.claim(fixed)
        for i, chapter in enumerate(sections):
            key = self.claim(chapter['id'])
            nav.append(f'<a href="#{key}"><span>{i:02}</span>{esc(chapter.get("nav", chapter["title"]))}</a>')
            chapters.append(f'<section class="chapter" id="{key}"><div class="chapter-head"><span class="chapter-no">{i:02}</span><div><div class="kicker">{esc(chapter.get("eyebrow", ""))}</div><h2>{esc(chapter["title"])}</h2></div></div><p class="chapter-intro">{esc(chapter.get("intro", ""))}</p>{self.blocks(chapter["blocks"])}</section>')
        css = (TEMPLATE/'style.css').read_text()
        js = (TEMPLATE/'app.js').read_text()
        style = '<style>'+css+'</style>' if self.single else '<link rel="stylesheet" href="style.css">'
        script_head = '' if self.single else '<script src="app.js" defer></script>'
        script_end = '<script>'+js.replace('</script', '<\\/script')+'</script>' if self.single else ''
        actions = []
        for i, action in enumerate(self.meta.get('actions', [])):
            target = ident(action['target'])
            if target not in self.ids: raise ValueError(f'Action target does not exist: {target}')
            actions.append(f'<a class="btn {"primary" if i==0 else ""}" href="#{target}">{esc(action["label"])} ↓</a>')
        snapshot = self.meta.get('snapshot', (self.commit[:7] if self.commit else 'illustrative example'))
        values = dict(lang=esc(self.meta.get('lang', 'ja')), title=esc(self.meta['title']), description=esc(self.meta.get('description', self.meta['lead'])),
                      style=style, script_head=script_head, script_end=script_end,
                      storage_key=esc('catch-up-docs:'+ident(self.meta['guide_id'])+':v1'),
                      repo_name=esc(self.meta['repo_name']), short_name=esc(self.meta.get('short_name', self.meta['repo_name'])),
                      audience=esc(self.meta.get('audience', '開発参加のための技術教材')), snapshot=esc(snapshot), verified_at=esc(self.meta['verified_at']),
                      repo_link=external(self.repo, 'Repository') if self.repo else '', chapter_count=str(len(sections)), tech_count=str(self.tech_count), nav=''.join(nav),
                      heading='<br>'.join(esc(x) for x in self.meta.get('heading_lines', [self.meta['title']])), lead=esc(self.meta['lead']), actions=''.join(actions), chapters=''.join(chapters),
                      footer=esc(self.meta.get('footer', 'リポジトリの実装に基づく技術教材。確認日と根拠・未確認事項は本文を参照。')),
                      attribution='学習チェックはブラウザ内に保存。外部解析や外部スクリプトは使用しません。<br>Icons: '+external('https://github.com/simple-icons/simple-icons','Simple Icons')+' / '+external('https://github.com/awslabs/aws-icons-for-plantuml','AWS Icons for PlantUML'))
        template = (TEMPLATE/'page.html').read_text()
        page = re.sub(r'\{\{([a-z_]+)\}\}', lambda m: values[m[1]], template)
        notices = (ROOT/'assets/icons/LICENSES.txt').read_text().replace('--', '—')
        return page.replace('</body>', '<!-- BUNDLED ICON NOTICES\n'+notices+'\n-->\n</body>')

def build(input_path, output, mode):
    spec = json.loads(input_path.read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    produced = []
    if mode in ('static', 'both'):
        r = Renderer(spec, input_path.parent.resolve(), single=False)
        page = r.page()
        site = output/'site'
        site.mkdir(exist_ok=True)
        (site/'index.html').write_text(page, encoding='utf-8')
        for name in ['style.css', 'app.js']: shutil.copyfile(TEMPLATE/name, site/name)
        shutil.copyfile(ROOT/'assets/icons/LICENSES.txt', site/'NOTICE-ICONS.txt')
        for key, path in r.used_icons.items():
            dest = site/'assets/icons'/f'{key}{path.suffix.lower()}'
            dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dest)
        for key, svg in r.diagrams.items():
            dest = site/'diagrams'/f'{key}.svg'
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(svg, encoding='utf-8')
        produced.append(str(site/'index.html'))
    if mode in ('single', 'both'):
        r = Renderer(spec, input_path.parent.resolve(), single=True)
        (output/'guide.html').write_text(r.page(), encoding='utf-8')
        produced.append(str(output/'guide.html'))
    return {'format':mode, 'artifacts':produced, 'chapters':len(spec['chapters']), 'technology_notes':r.tech_count, 'diagrams':len(r.diagrams)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='JSON guide specification')
    parser.add_argument('--output', type=Path, required=True, help='Artifact output directory, outside the analyzed repository')
    parser.add_argument('--format', choices=['static', 'single', 'both'], default='both')
    args = parser.parse_args()
    try:
        result = build(args.input.resolve(), args.output.resolve(), args.format)
    except (ValueError, KeyError, OSError, ET.ParseError) as exc:
        parser.exit(2, f'Cannot render guide: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
