// Phone nudge actions (render-product-pages.py, `nudge` block). A desktop
// app's page, opened on a phone (QR scan, TikTok link), offers to carry the
// page to the machine that can install it. The URL is the canonical page,
// no ?ref=, so what gets saved is the real one.
(function () {
  document.querySelectorAll('.phone-nudge[data-url]').forEach(function (box) {
    var url = box.getAttribute('data-url');
    var done = box.querySelector('.done');
    var copy = box.querySelector('.nudge-copy');
    var share = box.querySelector('.nudge-share');
    copy.addEventListener('click', function () {
      var ok = function () { done.textContent = 'copied'; };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, function () { window.prompt('Copy this link', url); });
      else window.prompt('Copy this link', url);
    });
    if (navigator.share) {
      share.addEventListener('click', function () {
        navigator.share({ title: box.getAttribute('data-title'), text: box.getAttribute('data-text'), url: url }).catch(function () {});
      });
    } else {
      share.hidden = true;
    }
  });
})();
