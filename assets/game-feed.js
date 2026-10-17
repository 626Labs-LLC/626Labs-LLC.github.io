// The 626 Mod Launcher's supported games, live (render-product-pages.py,
// `gameFeed` block). Reads the same signed game feed the app reads, off
// raw.githubusercontent.com: featured covers, then the engine-curated and
// Nexus-identified rows, and the counts into the hero's fine line. On a
// failed fetch or an unknown schema the fallback shows instead.
(function () {
  var root = document.querySelector('.game-feed[data-feed]');
  if (!root) return;
  var FEED = root.getAttribute('data-feed');
  var fine = document.getElementById('hero-fine');

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function coverUrl(steamAppId) {
    return 'https://cdn.cloudflare.steamstatic.com/steam/apps/' + steamAppId + '/library_600x900.jpg';
  }

  // Cover frame: real art when the CDN has it; the launcher's own placeholder language
  // (initial on the field, cyan/magenta paired) when it doesn't. Never a broken image.
  function coverFrame(game, rank) {
    var frame = el('div', 'cover-frame');
    frame.appendChild(el('div', 'cover-ph', (game.name || '?').trim().charAt(0).toUpperCase()));
    if (game.steamAppId) {
      var img = document.createElement('img');
      img.loading = 'lazy';
      img.alt = game.name + ' cover art';
      img.addEventListener('error', function () { img.remove(); });
      img.src = coverUrl(game.steamAppId);
      frame.appendChild(img);
    }
    if (rank != null) frame.appendChild(el('span', 'cover-rank', '#' + rank));
    return frame;
  }

  function gameRow(game, curated) {
    var row = el('div', 'row');
    row.appendChild(el('span', 'name', game.name));
    if (curated && game.engine) row.appendChild(el('span', 'chip', game.engine));
    if (!curated) row.appendChild(el('span', 'chip magenta', 'nexus'));
    row.appendChild(el('span', 'spacer'));
    var links = el('div', 'rlinks');
    if (game.steamUrl) {
      var s = el('a', null, 'Steam'); s.href = game.steamUrl; s.rel = 'noopener'; links.appendChild(s);
    }
    if (game.nexusUrl) {
      var n = el('a', null, 'Nexus'); n.href = game.nexusUrl; n.rel = 'noopener'; links.appendChild(n);
    }
    row.appendChild(links);
    return row;
  }

  function list(name) { return root.querySelector('[data-list="' + name + '"]'); }

  function render(data) {
    var c = data.counts || {};
    if (fine) {
      fine.innerHTML = '';
      fine.appendChild(el('b', null, String(c.total || data.games.length) + ' games'));
      fine.append(' · ' + (c.engineCurated || 0) + ' engine-curated · ' + (c.nexusOnly || 0) + ' Nexus-identified');
      if (data.generatedUtc) fine.append(' · feed updated ' + data.generatedUtc.slice(0, 10));
    }

    data.games.filter(function (g) { return typeof g.featured === 'number'; })
      .sort(function (a, b) { return a.featured - b.featured; })
      .forEach(function (g) {
        var card = el('div', 'cover-card');
        card.appendChild(coverFrame(g, g.featured));
        card.appendChild(el('div', 'cover-name', g.name));
        if (g.engine) card.appendChild(el('div', 'cover-eng', g.engine));
        list('featured').appendChild(card);
      });

    var curatedN = 0, nexusN = 0;
    data.games.forEach(function (g) {
      if (g.tier === 'engine-curated') { list('curated').appendChild(gameRow(g, true)); curatedN++; }
      else if (g.tier === 'nexus-only') { list('nexus').appendChild(gameRow(g, false)); nexusN++; }
    });
    document.getElementById('curated-count').textContent = curatedN + ' games';
    document.getElementById('nexus-count').textContent = nexusN + ' games';

    root.querySelector('.loading').hidden = true;
    root.querySelector('.feed-content').hidden = false;
  }

  function fail() {
    root.querySelector('.loading').hidden = true;
    root.querySelector('.fallback').hidden = false;
    if (fine) fine.textContent = 'live list unavailable — see GitHub below';
  }

  fetch(FEED)
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      if (!data || data.schemaVersion !== 1 || !Array.isArray(data.games)) throw new Error('schema');
      render(data);
    })
    .catch(fail);
})();
