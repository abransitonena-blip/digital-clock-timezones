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
      el.style.transitionDelay = (i * 0.1) + 's';
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

  // ---------- soft sound feedback (no audio file, synthesized) ----------

  var audioCtx = null;
  function playTone(kind) {
    if (prefersReducedMotion) return;
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (audioCtx.state === 'suspended') audioCtx.resume();
      var now = audioCtx.currentTime;
      var osc = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      var range = kind === 'reveal' ? [560, 900] : kind === 'flip' ? [720, 640] : [520, 760];
      osc.type = 'sine';
      osc.frequency.setValueAtTime(range[0], now);
      osc.frequency.exponentialRampToValueAtTime(range[1], now + 0.12);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.05, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.26);
      osc.start(now);
      osc.stop(now + 0.3);
    } catch (e) {
      /* Web Audio not available; fail silently */
    }
  }

  // ---------- flower/heart burst (reusable) ----------

  function burstAt(originX, originY) {
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
  }

  var burstBtn = document.querySelector('.burst-btn');
  if (burstBtn) {
    burstBtn.addEventListener('click', function () {
      var rect = burstBtn.getBoundingClientRect();
      burstAt(rect.left + rect.width / 2, rect.top + rect.height / 2);
      playTone('burst');
    });
  }

  // ---------- flip cards: "razones" ----------

  var reasonCards = document.querySelectorAll('.reason-card');
  reasonCards.forEach(function (card) {
    card.addEventListener('click', function () {
      var flipped = card.classList.toggle('flipped');
      card.setAttribute('aria-pressed', flipped ? 'true' : 'false');
      playTone('flip');
    });
  });

  // ---------- scratch-to-reveal secret message ----------

  (function initScratch() {
    var canvas = document.getElementById('scratch-canvas');
    if (!canvas || !canvas.getContext) return;
    var wrap = canvas.closest('.scratch-wrap');
    var ctx = canvas.getContext('2d', { willReadFrequently: true });
    var dpr = window.devicePixelRatio || 1;
    var revealed = false;
    var scratching = false;

    function drawScratchLayer(w, h) {
      ctx.globalCompositeOperation = 'source-over';
      var grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, '#f6cf7c');
      grad.addColorStop(1, '#e2a63f');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = 'rgba(92,67,38,.85)';
      ctx.font = '600 ' + Math.max(14, Math.min(18, w * 0.045)) + 'px Quicksand, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('Raspa aquí 👆', w / 2, h / 2);
    }

    function sizeCanvas() {
      if (revealed) return;
      var rect = wrap.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = rect.width + 'px';
      canvas.style.height = rect.height + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawScratchLayer(rect.width, rect.height);
    }

    function scratchAt(x, y) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath();
      ctx.arc(x, y, 22, 0, Math.PI * 2);
      ctx.fill();
    }

    function getPos(e) {
      var rect = canvas.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    function revealAll() {
      revealed = true;
      canvas.style.transition = 'opacity .6s ease';
      canvas.style.opacity = '0';
      setTimeout(function () { canvas.style.display = 'none'; }, 650);
      var rect = wrap.getBoundingClientRect();
      burstAt(rect.left + rect.width / 2, rect.top + rect.height / 2);
      playTone('reveal');
    }

    function checkProgress() {
      var w = canvas.width, h = canvas.height;
      if (!w || !h) return;
      var data;
      try {
        data = ctx.getImageData(0, 0, w, h).data;
      } catch (e) {
        return;
      }
      var cleared = 0, total = 0;
      for (var i = 3; i < data.length; i += 4 * 37) {
        total++;
        if (data[i] < 80) cleared++;
      }
      if (total && cleared / total > 0.5) revealAll();
    }

    function handleDown(e) {
      if (revealed) return;
      scratching = true;
      scratchAt(getPos(e).x, getPos(e).y);
    }
    function handleMove(e) {
      if (!scratching || revealed) return;
      e.preventDefault();
      scratchAt(getPos(e).x, getPos(e).y);
      checkProgress();
    }
    function handleUp() { scratching = false; }

    canvas.addEventListener('pointerdown', handleDown);
    canvas.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
    window.addEventListener('resize', sizeCanvas);

    if (prefersReducedMotion) {
      canvas.style.display = 'none';
    } else {
      sizeCanvas();
    }
  })();

  // ---------- memory match game: "encuentra las parejas" ----------

  (function initMemory() {
    var grid = document.getElementById('memory-grid');
    var movesEl = document.getElementById('memory-moves');
    var winEl = document.getElementById('memory-win');
    var resetBtn = document.getElementById('memory-reset');
    if (!grid) return;

    var ICONS = ['🌼', '💛', '🌻', '✨', '💐', '😊'];
    var state = { first: null, second: null, lock: false, matches: 0, moves: 0 };

    function shuffle(arr) {
      for (var i = arr.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
      }
      return arr;
    }

    function updateMoves() {
      if (movesEl) movesEl.textContent = 'Movimientos: ' + state.moves;
    }

    function handleClick(card) {
      if (state.lock || card === state.first || card.classList.contains('matched')) return;
      card.classList.add('flipped');
      playTone('flip');

      if (!state.first) {
        state.first = card;
        return;
      }
      state.second = card;
      state.lock = true;
      state.moves++;
      updateMoves();

      if (state.first.dataset.icon === state.second.dataset.icon) {
        state.first.classList.add('matched');
        state.second.classList.add('matched');
        state.matches++;
        state.first = null;
        state.second = null;
        state.lock = false;
        if (state.matches === ICONS.length) onWin();
      } else {
        var f = state.first, s = state.second;
        setTimeout(function () {
          f.classList.remove('flipped');
          s.classList.remove('flipped');
          state.first = null;
          state.second = null;
          state.lock = false;
        }, 800);
      }
    }

    function onWin() {
      playTone('reveal');
      if (winEl) winEl.classList.add('visible');
      var rect = grid.getBoundingClientRect();
      burstAt(rect.left + rect.width / 2, rect.top + rect.height / 2);
    }

    function buildGrid() {
      grid.innerHTML = '';
      state.first = null;
      state.second = null;
      state.lock = false;
      state.matches = 0;
      state.moves = 0;
      updateMoves();
      if (winEl) winEl.classList.remove('visible');

      var deck = shuffle(ICONS.concat(ICONS));
      deck.forEach(function (icon) {
        var card = document.createElement('button');
        card.type = 'button';
        card.className = 'memory-card';
        card.dataset.icon = icon;
        card.innerHTML =
          '<span class="memory-card-inner">' +
            '<span class="memory-face memory-front">💛</span>' +
            '<span class="memory-face memory-back">' + icon + '</span>' +
          '</span>';
        card.addEventListener('click', function () { handleClick(card); });
        grid.appendChild(card);
      });
    }

    if (resetBtn) resetBtn.addEventListener('click', buildGrid);
    buildGrid();
  })();

  // ---------- cursor heart trail (desktop only) ----------

  if (!prefersReducedMotion && window.matchMedia('(pointer: fine)').matches) {
    var lastTrail = 0;
    window.addEventListener('pointermove', function (e) {
      var now = Date.now();
      if (now - lastTrail < 100) return;
      lastTrail = now;
      var h = document.createElement('span');
      h.className = 'cursor-heart';
      h.textContent = Math.random() > 0.5 ? '💛' : '🌼';
      h.style.left = e.clientX + 'px';
      h.style.top = e.clientY + 'px';
      document.body.appendChild(h);
      h.addEventListener('animationend', function () { h.remove(); });
    });
  }
})();
