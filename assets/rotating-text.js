/* RotatingText (React Bits) — ported to vanilla JS.
   No React, no motion/framer: uses the Web Animations API, which gives the
   same staggered enter/exit without adding a build step to this site.

   Markup:
     <span data-rotating-text data-texts="First|Second|Third">First</span>

   The static contents of the element are used as the first frame, so crawlers
   and no-JS visitors still see real text. */

const DEFAULTS = {
  interval: 2000,
  duration: 400,
  easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
  stagger: 0.025,          // seconds between characters, matching the React prop
  staggerFrom: 'first',    // first | last | center | random | <number>
  splitBy: 'characters',   // characters | words | lines | <separator>
  loop: true,
  auto: true,
  initial: { y: '100%', opacity: 0 },
  animate: { y: '0%', opacity: 1 },
  exit: { y: '-120%', opacity: 0 }
};

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function splitIntoCharacters(text) {
  if (typeof Intl !== 'undefined' && Intl.Segmenter) {
    const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
    return Array.from(segmenter.segment(text), s => s.segment);
  }
  return Array.from(text);
}

function splitText(text, splitBy) {
  if (splitBy === 'characters') {
    const words = text.split(' ');
    return words.map((word, i) => ({
      characters: splitIntoCharacters(word),
      needsSpace: i !== words.length - 1
    }));
  }
  if (splitBy === 'words') {
    return text.split(' ').map((word, i, arr) => ({
      characters: [word],
      needsSpace: i !== arr.length - 1
    }));
  }
  if (splitBy === 'lines') {
    return text.split('\n').map((line, i, arr) => ({
      characters: [line],
      needsSpace: i !== arr.length - 1
    }));
  }
  return text.split(splitBy).map((part, i, arr) => ({
    characters: [part],
    needsSpace: i !== arr.length - 1
  }));
}

function frame(state) {
  return {
    transform: `translateY(${state.y})`,
    opacity: String(state.opacity)
  };
}

export default class RotatingText {
  constructor(el, options = {}) {
    this.el = el;
    this.opts = { ...DEFAULTS, ...options };
    this.texts = this.opts.texts || [];
    this.index = 0;
    this.timer = null;
    this.busy = false;
    this.visible = true;

    if (this.texts.length === 0) return;

    this.el.classList.add('text-rotate');

    this.srOnly = document.createElement('span');
    this.srOnly.className = 'text-rotate-sr-only';

    this.stage = document.createElement('span');
    this.stage.className =
      this.opts.splitBy === 'lines' ? 'text-rotate-lines' : 'text-rotate';
    this.stage.setAttribute('aria-hidden', 'true');

    this.el.textContent = '';
    this.el.append(this.srOnly, this.stage);
    this.render(0);

    // WCAG 2.2.2: auto-updating text is motion. Show the first item and stop.
    if (reduceMotion.matches) return;

    if ('IntersectionObserver' in window) {
      this.io = new IntersectionObserver(entries => {
        this.visible = entries[0].isIntersecting;
        this.sync();
      }, { threshold: 0 });
      this.io.observe(this.el);
    }
    document.addEventListener('visibilitychange', () => this.sync());

    if (this.opts.auto) this.start();
  }

  render(index) {
    this.srOnly.textContent = this.texts[index];
    this.stage.textContent = '';

    const groups = splitText(this.texts[index], this.opts.splitBy);
    const total = groups.reduce((sum, g) => sum + g.characters.length, 0);
    const elements = [];
    let seen = 0;

    for (const group of groups) {
      const wordEl = document.createElement('span');
      wordEl.className = 'text-rotate-word';
      for (const char of group.characters) {
        const charEl = document.createElement('span');
        charEl.className = 'text-rotate-element';
        charEl.textContent = char;
        charEl.dataset.delay = String(this.staggerDelay(seen++, total));
        wordEl.appendChild(charEl);
        elements.push(charEl);
      }
      if (group.needsSpace) {
        const space = document.createElement('span');
        space.className = 'text-rotate-space';
        space.textContent = ' ';
        wordEl.appendChild(space);
      }
      this.stage.appendChild(wordEl);
    }
    return elements;
  }

  staggerDelay(index, total) {
    const step = this.opts.stagger * 1000;
    const from = this.opts.staggerFrom;
    if (from === 'first') return index * step;
    if (from === 'last') return (total - 1 - index) * step;
    if (from === 'center') return Math.abs(Math.floor(total / 2) - index) * step;
    if (from === 'random') {
      return Math.abs(Math.floor(Math.random() * total) - index) * step;
    }
    return Math.abs(Number(from) - index) * step;
  }

  /* Runs one staggered pass and resolves when the last character lands —
     this is the vanilla stand-in for AnimatePresence mode="wait". */
  animateAll(elements, from, to) {
    const { duration, easing } = this.opts;
    let last = 0;
    for (const el of elements) {
      const delay = Number(el.dataset.delay) || 0;
      last = Math.max(last, delay);
      el.animate([frame(from), frame(to)], {
        duration, delay, easing, fill: 'both'
      });
    }
    return new Promise(resolve => setTimeout(resolve, last + duration));
  }

  async goTo(index) {
    if (this.busy || index === this.index) return;
    this.busy = true;

    const current = Array.from(this.stage.querySelectorAll('.text-rotate-element'));
    await this.animateAll(current, this.opts.animate, this.opts.exit);

    this.index = index;
    const next = this.render(index);
    await this.animateAll(next, this.opts.initial, this.opts.animate);

    this.busy = false;
    if (this.opts.onNext) this.opts.onNext(index);
  }

  next() {
    const last = this.texts.length - 1;
    if (this.index === last) {
      if (this.opts.loop) this.goTo(0);
      return;
    }
    this.goTo(this.index + 1);
  }

  previous() {
    if (this.index === 0) {
      if (this.opts.loop) this.goTo(this.texts.length - 1);
      return;
    }
    this.goTo(this.index - 1);
  }

  reset() { this.goTo(0); }

  start() {
    if (this.timer) return;
    this.timer = setInterval(() => this.next(), this.opts.interval);
  }

  stop() {
    clearInterval(this.timer);
    this.timer = null;
  }

  /* Don't burn frames on a tab nobody is looking at. */
  sync() {
    if (!this.opts.auto) return;
    if (this.visible && !document.hidden) this.start();
    else this.stop();
  }
}

function readOptions(el) {
  const d = el.dataset;
  const opts = { texts: (d.texts || '').split('|').map(t => t.trim()).filter(Boolean) };
  if (d.interval) opts.interval = Number(d.interval);
  if (d.duration) opts.duration = Number(d.duration);
  if (d.stagger) opts.stagger = Number(d.stagger);
  if (d.staggerFrom) opts.staggerFrom = d.staggerFrom;
  if (d.splitBy) opts.splitBy = d.splitBy;
  if (d.easing) opts.easing = d.easing;
  if (d.loop) opts.loop = d.loop !== 'false';
  if (d.auto) opts.auto = d.auto !== 'false';
  return opts;
}

document.querySelectorAll('[data-rotating-text]').forEach(el => {
  el.rotatingText = new RotatingText(el, readOptions(el));
});
