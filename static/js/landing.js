(function () {
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var triggers = [];

  function revealStatic() {
    document.querySelectorAll(
      '#hero-eyebrow, #hero-heading, #hero-desc, #hero-actions, #hero-stats, #hero-visual, .reveal'
    ).forEach(function (el) {
      el.style.opacity = 1;
      el.style.transform = 'none';
    });
    document.querySelectorAll('.story-block').forEach(function (el) {
      el.style.opacity = 1;
    });
  }

  if (prefersReduced) {
    revealStatic();
    return;
  }

  gsap.set(['#hero-eyebrow', '#hero-heading', '#hero-desc', '#hero-actions', '#hero-stats'], { y: 24 });

  var heroTl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  heroTl
    .to('#hero-eyebrow', { opacity: 1, y: 0, duration: .6, delay: .1 })
    .to('#hero-heading', { opacity: 1, y: 0, duration: .8 }, '-=.35')
    .to('#hero-desc', { opacity: 1, y: 0, duration: .6 }, '-=.45')
    .to('#hero-actions', { opacity: 1, y: 0, duration: .5 }, '-=.35')
    .to('#hero-visual', { opacity: 1, scale: 1, duration: .9, ease: 'power2.out' }, '-=.7')
    .to('#hero-stats', { opacity: 1, y: 0, duration: .5 }, '-=.3');

  gsap.utils.toArray('.reveal').forEach(function (el) {
    var t = gsap.fromTo(el,
      { opacity: 0, y: 28 },
      {
        opacity: 1, y: 0, duration: .7, ease: 'power2.out',
        scrollTrigger: { trigger: el, start: 'top 88%', toggleActions: 'play none none none' }
      }
    );
    triggers.push(t.scrollTrigger);
  });

  var tiltCard = document.getElementById('hero-tilt-card');
  var tiltScene = document.getElementById('hero-visual');
  if (tiltCard && tiltScene && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    var maxTilt = 6;
    tiltScene.addEventListener('mousemove', function (e) {
      var rect = tiltScene.getBoundingClientRect();
      var px = (e.clientX - rect.left) / rect.width - 0.5;
      var py = (e.clientY - rect.top) / rect.height - 0.5;
      gsap.to(tiltCard, {
        rotateY: px * maxTilt,
        rotateX: -py * maxTilt,
        duration: .4,
        ease: 'power2.out',
        overwrite: true
      });
    });
    tiltScene.addEventListener('mouseleave', function () {
      gsap.to(tiltCard, { rotateY: 0, rotateX: 0, duration: .6, ease: 'power2.out' });
    });
  }

  var storyPin = document.getElementById('story-pin');
  var storyBlocks = document.querySelectorAll('.story-block');
  var storyFrames = document.querySelectorAll('.story-visual-frame');

  if (storyPin && storyBlocks.length && window.innerWidth > 1024) {
    storyBlocks.forEach(function (block, i) {
      var t = ScrollTrigger.create({
        trigger: block,
        start: 'top center',
        end: 'bottom center',
        onEnter: function () { setActiveStory(i); },
        onEnterBack: function () { setActiveStory(i); }
      });
      triggers.push(t);
    });
  }

  function setActiveStory(index) {
    storyBlocks.forEach(function (b, i) {
      b.classList.toggle('active', i === index);
    });
    storyFrames.forEach(function (f) {
      f.classList.toggle('active', Number(f.dataset.storyFrame) === index);
    });
  }

  document.querySelectorAll('a[href^="/dashboard"], a[href^="/register"], a[href^="/login"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = this.getAttribute('href');
      if (!href || href.startsWith('#')) return;
      e.preventDefault();
      gsap.to('body', {
        opacity: 0, duration: .22, ease: 'power1.in',
        onComplete: function () { window.location.href = href; }
      });
    });
  });
  gsap.fromTo('body', { opacity: 0 }, { opacity: 1, duration: .3, ease: 'power1.out' });

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      ScrollTrigger.refresh();
    }, 250);
  });
})();
