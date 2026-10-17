// Language pills under a launch video (render-product-pages.py, `video`
// block). Same trailer, several voices: a pill swaps the source, poster and
// caption to <base>-<lang>-16x9.mp4 and <base>-poster-<lang>.jpg. Each
// localized cut carries Este's voice on the ElevenLabs multilingual model
// plus the app captured in that language. The first pill is the default cut.
(function () {
  document.querySelectorAll('.video-frame[data-base]').forEach(function (frame) {
    var video = frame.querySelector('video');
    var cap = frame.querySelector('p.video-cap');
    var pills = frame.querySelectorAll('.lang-pill');
    var base = frame.getAttribute('data-base');
    var cut = frame.getAttribute('data-cut');
    var defaultCap = cap.innerHTML;
    pills.forEach(function (p) {
      p.addEventListener('click', function () {
        if (p.classList.contains('is-active')) return;
        pills.forEach(function (q) { q.classList.remove('is-active'); });
        p.classList.add('is-active');
        var lang = p.getAttribute('data-lang');
        var suffix = lang ? '-' + lang : '';
        video.pause();
        video.poster = base + '-poster' + suffix + '.jpg';
        video.querySelector('source').src = base + suffix + '-16x9.mp4';
        video.load();
        if (lang) cap.textContent = cut + ' · ' + p.getAttribute('data-secs') + ' seconds · ' + p.textContent;
        else cap.innerHTML = defaultCap;
      });
    });
  });
})();
