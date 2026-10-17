// RoRoRo plugins, live (render-product-pages.py, `pluginCatalog` and
// `pluginList` blocks). Reads data/rororo-plugins.json, the nightly copy of
// the catalog the app itself reads, enriched with each plugin's live
// release. The marketplace page builds a card per plugin; the product page
// adds a row per live plugin ahead of its bench. Either page also takes the
// current host version and Store/download links. On any failure the static
// content stands (the marketplace shows its fallback): this only ever
// upgrades the page.
(function () {
  var catalog = document.querySelector('.plugin-cards');
  var list = document.querySelector('.live-plugins');
  if (!catalog && !list && !document.getElementById('win-latest')) return;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function icons(mount) {
    try { return JSON.parse(mount.getAttribute('data-icons') || '{}'); } catch (e) { return {}; }
  }

  var toastTimer = null;
  function toast(html) {
    var t = document.querySelector('.toast');
    if (!t) return;
    t.innerHTML = html;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('show'); }, 3600);
  }

  function monogram(name) {
    var words = name.replace(/^RoRoRo\s+/i, '').split(/\s+/);
    return words.slice(0, 2).map(function (w) { return w[0]; }).join('').toUpperCase();
  }

  function avatarFor(p, ICONS) {
    if (ICONS[p.id]) {
      var av = el('div', 'avatar family');
      var im = document.createElement('img');
      im.src = ICONS[p.id];
      im.alt = '';
      av.appendChild(im);
      return av;
    }
    return el('div', 'avatar', monogram(p.name));
  }

  // The meters for the family plugins are parked in a <template> in the
  // page (so the repo-activity bot can find their repos). The cards are
  // built long after meter.js ran once and found nothing; load it again.
  function meterFor(id) {
    var tpl = document.querySelector('template.plugin-meters');
    if (!tpl) return null;
    var m = tpl.content.querySelector('[data-plugin="' + id + '"]');
    return m ? m.cloneNode(true) : null;
  }
  function fillMeters() {
    var s = document.createElement('script');
    s.src = '/repo-meter/meter.js';
    document.body.appendChild(s);
  }

  function renderCatalog(data) {
    var ICONS = icons(catalog);
    data.plugins.forEach(function (p) {
      var card = el('div', 'plugin-card');

      var head = el('div', 'head');
      head.appendChild(avatarFor(p, ICONS));
      var titleWrap = el('div', 'title');
      titleWrap.appendChild(el('h3', null, p.name));
      titleWrap.appendChild(el('span', 'ver', 'v' + p.version));
      head.appendChild(titleWrap);
      card.appendChild(head);

      card.appendChild(el('p', 'desc', p.description));

      var meta = el('div', 'meta');
      if (p.releasedAt) {
        var m1 = el('span'); m1.append('updated '); m1.appendChild(el('b', null, p.releasedAt));
        meta.appendChild(m1);
      }
      if (p.minHostVersion) {
        var m2 = el('span'); m2.append('needs RoRoRo ');
        m2.appendChild(el('b', null, p.minHostVersion.replace(/(\.0)+$/, '') + '+'));
        meta.appendChild(m2);
      }
      if (typeof p.installs === 'number' && p.installs > 0) {
        var m3 = el('span'); m3.appendChild(el('b', null, String(p.installs))); m3.append(' installs');
        meta.appendChild(m3);
      }
      card.appendChild(meta);

      var meter = meterFor(p.id);
      if (meter) card.appendChild(meter);

      var actions = el('div', 'actions');
      var copyBtn = el('button', 'btn primary', 'Copy install URL');
      copyBtn.type = 'button';
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(p.installUrl).then(function () {
          toast('Copied. In RoRoRo: <b>Plugins &rarr; Install</b>, paste, go.');
        }, function () {
          toast('Copy blocked — the URL is: <b>' + p.installUrl + '</b>');
        });
      });
      actions.appendChild(copyBtn);
      var zip = el('a', 'btn', 'plugin.zip');
      zip.href = p.zipUrl;
      actions.appendChild(zip);
      var src = el('a', 'btn', 'Source');
      src.href = p.repoUrl;
      actions.appendChild(src);
      card.appendChild(actions);

      catalog.appendChild(card);
    });
    fillMeters();
  }

  function renderList(data) {
    var ICONS = icons(list);
    data.plugins.forEach(function (p) {
      var card = el('div', 'plugin live');
      var l = el('div', 'pl-l');
      var nameRow = el('div', 'pl-name');
      if (ICONS[p.id]) {
        var ic = document.createElement('img');
        ic.src = ICONS[p.id];
        ic.alt = '';
        ic.className = 'pl-icon';
        nameRow.appendChild(ic);
      }
      nameRow.appendChild(el('h4', null, p.name));
      nameRow.appendChild(el('span', 'status live', 'Live · v' + p.version));
      l.appendChild(nameRow);
      l.appendChild(el('p', null, p.description));
      var link = el('a', 'pl-link', list.getAttribute('data-label') + ' ');
      link.href = list.getAttribute('data-href');
      link.insertAdjacentHTML('beforeend', '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7M7 7h10v10"/></svg>');
      card.appendChild(l);
      card.appendChild(link);
      list.appendChild(card);
    });
  }

  function renderHost(host) {
    if (!host) return;
    var ver = document.getElementById('host-ver');
    if (ver && host.version) ver.textContent = 'v' + host.version + ' current';
    var latest = document.getElementById('win-latest');
    if (latest && host.version) latest.textContent = 'v' + host.version.replace(/(\.0)+$/, '');
    var store = document.getElementById('host-store');
    if (store && host.storeUrl) store.href = host.storeUrl;
    var setup = document.getElementById('host-setup');
    if (setup && host.setupUrl) setup.href = host.setupUrl;
  }

  fetch('/data/rororo-plugins.json')
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      renderHost(data.host);
      if (catalog) renderCatalog(data);
      if (list && data.plugins) renderList(data);
    })
    .catch(function () {
      var fb = document.querySelector('.plugin-fallback');
      if (fb) fb.hidden = false;
    });
})();
