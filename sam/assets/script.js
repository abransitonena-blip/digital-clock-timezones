(function () {
  var EMOJIS = ['🌼', '💛', '🌻', '✨', '💐'];
  var container = document.getElementById('floaties');
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function spawnFloaty() {
    if (!container) return;
    var el = document.createElement('span');
    el.className = 'floaty';
    el.textContent = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
    var size = 1 + Math.random() * 1.6;
    var duration = 9 + Math.random() * 8;
    var drift = (Math.random() * 200 - 100).toFixed(0) + 'px';
    el.style.left = Math.random() * 100 + 'vw';
    el.style.fontSize = size + 'rem';
    el.style.setProperty('--drift', drift);
    el.style.animationDuration = duration + 's';
    el.addEventListener('animationend', function () { el.remove(); });
    container.appendChild(el);
  }

  var spawnTimer = null;
  if (!prefersReducedMotion) {
    spawnTimer = setInterval(spawnFloaty, 650);
    for (var i = 0; i < 6; i++) {
      setTimeout(spawnFloaty, i * 200);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        clearInterval(spawnTimer);
      } else {
        spawnTimer = setInterval(spawnFloaty, 650);
      }
    });
  }

  var revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length && 'IntersectionObserver' in window) {
    revealEls.forEach(function (el, i) {
      el.style.transitionDelay = (i * 0.15) + 's';
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('visible'); });
  }

  var burstBtn = document.querySelector('.burst-btn');
  if (burstBtn) {
    burstBtn.addEventListener('click', function () {
      var rect = burstBtn.getBoundingClientRect();
      var originX = rect.left + rect.width / 2;
      var originY = rect.top + rect.height / 2;
      var count = 18;
      for (var i = 0; i < count; i++) {
        var p = document.createElement('span');
        p.className = 'burst-particle';
        p.textContent = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
        var angle = Math.random() * Math.PI * 2;
        var dist = 80 + Math.random() * 140;
        p.style.left = originX + 'px';
        p.style.top = originY + 'px';
        p.style.fontSize = (1 + Math.random()) + 'rem';
        p.style.setProperty('--tx', Math.cos(angle) * dist + 'px');
        p.style.setProperty('--ty', Math.sin(angle) * dist + 'px');
        document.body.appendChild(p);
        p.addEventListener('animationend', function () { this.remove(); });
      }
      if (!prefersReducedMotion) spawnFloaty();
    });
  }
})();
