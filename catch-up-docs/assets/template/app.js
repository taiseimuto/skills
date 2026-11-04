'use strict';
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const readData = el => JSON.parse($('.widget-data', el).textContent);
  const storage = {
    get(k, fallback) { try { return JSON.parse(localStorage.getItem(k)) ?? fallback; } catch { return fallback; } },
    set(k, value) { try { localStorage.setItem(k, JSON.stringify(value)); } catch { /* file/private mode may deny storage */ } }
  };
  const toast = message => {
    const el = $('#toast'); el.textContent = message; el.hidden = false;
    clearTimeout(toast.timer); toast.timer = setTimeout(() => { el.hidden = true; }, 2300);
  };
  const nav = $('.sidebar');
  const setNav = open => {
    document.body.classList.toggle('nav-open', open);
    $('#menu').setAttribute('aria-expanded', String(open));
    if (open) $('#close-nav').focus(); else $('#menu').focus();
  };
  $('#menu').addEventListener('click', () => setNav(!document.body.classList.contains('nav-open')));
  $('#close-nav').addEventListener('click', () => setNav(false));
  $('#overlay').addEventListener('click', () => setNav(false));
  $$('.sidebar nav a').forEach(a => a.addEventListener('click', () => {
    document.body.classList.remove('nav-open'); $('#menu').setAttribute('aria-expanded', 'false');
    const target = document.getElementById(a.hash.slice(1));
    if (target) { target.tabIndex = -1; target.focus({ preventScroll: true }); }
  }));
  document.addEventListener('keydown', e => {
    if (!document.body.classList.contains('nav-open')) return;
    if (e.key === 'Escape') setNav(false);
    if (e.key === 'Tab') {
      const focusable = $$('a,button', nav), first = focusable[0], last = focusable.at(-1);
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  $$('.code-wrap').forEach(w => {
    const button = document.createElement('button'); button.className = 'copy'; button.type = 'button';
    button.textContent = 'COPY'; button.setAttribute('aria-label', 'コードをコピー');
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText($('code', w).textContent); toast('コピーしました'); }
      catch { toast('コピーできませんでした。コードを選択してください。'); }
    }); w.prepend(button);
  });
  $$('.tech-widget').forEach(widget => {
    const techs = $$('.tech', widget), search = $('input[type=search]', widget);
    search.addEventListener('input', () => {
      const term = search.value.trim().toLowerCase(); let count = 0;
      techs.forEach(d => { d.hidden = !d.textContent.toLowerCase().includes(term); if (!d.hidden) count++; });
      $$('.tech-group', widget).forEach(g => { g.hidden = !$$('.tech', g).some(d => !d.hidden); });
      $('.tech-empty', widget).hidden = count > 0;
      $('.tech-count', widget).textContent = term ? `${count} 件の技術が一致` : `${techs.length} 技術・ツール`;
    });
    $('[data-expand]', widget).addEventListener('click', () => techs.filter(d => !d.hidden).forEach(d => { d.open = true; }));
    $('[data-collapse]', widget).addEventListener('click', () => techs.forEach(d => { d.open = false; }));
  });
  $$('[data-tabs]').forEach(scope => {
    const controls = $$(':scope > .tabs button', scope), panels = $$(':scope > [data-tab-panel]', scope);
    controls.forEach(b => b.addEventListener('click', () => {
      controls.forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      panels.forEach(p => { p.hidden = p.id !== b.dataset.panel; });
    }));
  });
  const modal = $('#diagram-modal');
  $$('[data-zoom]').forEach(b => b.addEventListener('click', () => {
    const figure = document.getElementById(b.dataset.zoom);
    $('#modal-title').textContent = $('.diagram-toolbar span', figure).textContent;
    const clone = $('svg', figure).cloneNode(true);
    // Avoid duplicate document IDs when the accessible SVG is cloned into the dialog.
    $$('[id]', clone).forEach(el => {
      const old = el.id, next = old + '-zoom'; el.id = next;
      $$('[marker-end]', clone).forEach(p => { if (p.getAttribute('marker-end') === `url(#${old})`) p.setAttribute('marker-end', `url(#${next})`); });
    });
    clone.setAttribute('aria-labelledby', clone.getAttribute('aria-labelledby').split(' ').map(id => id + '-zoom').join(' '));
    $('#modal-content').replaceChildren(clone); modal.showModal();
  }));
  $('#close-diagram').addEventListener('click', () => modal.close());
  modal.addEventListener('click', e => { if (e.target === modal) modal.close(); });
  $$('.finder').forEach(widget => {
    const data = readData(widget), select = $('select', widget), out = $('.finder-result', widget);
    const show = () => {
      const item = data.items[Number(select.value)]; out.replaceChildren();
      const route = document.createElement('strong'); route.textContent = item.route || item.label;
      const file = document.createElement('code'); file.textContent = item.file;
      const description = document.createElement('p'); description.textContent = item.description;
      out.append(route, file, description);
      if (item.source_url) { const a = document.createElement('a'); a.textContent = '根拠のファイルを開く ↗'; a.href = item.source_url; a.target = '_blank'; a.rel = 'noopener noreferrer'; out.append(a); }
    }; select.addEventListener('change', show); show();
  });
  $$('.check-widget').forEach(widget => {
    const key = document.body.dataset.storageKey + ':' + widget.id;
    let saved = storage.get(key, {});
    if (saved === null || Array.isArray(saved) || typeof saved !== 'object') saved = {};
    const checks = $$('input[type=checkbox]', widget);
    const update = () => { $('.complete-count', widget).textContent = `${checks.filter(c => c.checked).length} / ${checks.length} 完了`; };
    checks.forEach(c => { c.checked = Boolean(saved[c.id]); c.addEventListener('change', () => { saved[c.id] = c.checked; storage.set(key, saved); update(); }); });
    $('[data-reset]', widget).addEventListener('click', () => { saved = {}; checks.forEach(c => { c.checked = false; }); storage.set(key, saved); update(); toast('チェックをリセットしました'); });
    update();
  });
  $$('.quiz').forEach(widget => {
    const data = readData(widget);
    $$('[data-answer]', widget).forEach(b => b.addEventListener('click', () => {
      const feedback = $('.feedback', widget); feedback.hidden = false;
      feedback.textContent = (Number(b.dataset.answer) === data.correct ? '正解。' : 'もう一度確認。') + data.explanation;
      $$('[data-answer]', widget).forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    }));
  });
  const anchors = $$('.sidebar nav a'), chapters = $$('section.chapter'); let scheduled = false;
  function updateProgress() {
    const total = document.documentElement.scrollHeight - innerHeight;
    const fraction = total > 0 ? Math.max(0, Math.min(1, scrollY / total)) : 0;
    const sidebarWidth = innerWidth > 760 ? nav.getBoundingClientRect().width : 0;
    $('#progress').style.width = `${fraction * (innerWidth - sidebarWidth)}px`;
    let current = chapters[0]; chapters.forEach(c => { if (c.getBoundingClientRect().top < 180) current = c; });
    anchors.forEach(a => { const active = current && a.hash === '#' + current.id; a.classList.toggle('active', active); if (active) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current'); });
    scheduled = false;
  }
  window.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); } }, { passive: true });
  window.addEventListener('resize', updateProgress); updateProgress();
})();
