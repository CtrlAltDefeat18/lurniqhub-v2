/**
 * LurniqHub Helm Simulator
 *
 * Canvas-based 2-D vessel simulation.  The player steers from a start
 * position, collecting sequential waypoints while avoiding hazards.
 * A simulated ocean current continuously pushes the vessel off course.
 *
 * Controls
 *   ← / A   :  turn to port (left)
 *   → / D   :  turn to starboard (right)
 *   ↑ / W   :  increase throttle
 *   ↓ / S   :  reduce throttle / brake
 *   Touch   :  on-screen buttons shown on narrow screens
 *
 * Config shape (from seed_data SEED_COURSES[n].simulation.config):
 *   world      { w, h }           world unit dimensions
 *   start      { x, y, heading }  heading in degrees (0 = north)
 *   vessel     { max_speed, turn_rate }
 *   current    { x, y }           world-units per frame drift
 *   time_par   number             seconds for a perfect run (time bonus)
 *   time_limit number             hard cutoff in seconds
 *   waypoints  [{ x, y, r, label }]  in order
 *   hazards    [{ x, y, r, label }]
 */

class HelmSimulator {
  constructor(canvas, cfg, onEnd) {
    // Basic config validation
    if (!canvas || !cfg || !cfg.world || !cfg.start || !cfg.vessel) {
      throw new Error('Invalid simulator config');
    }
    this.canvas  = canvas;
    this.ctx     = canvas.getContext('2d');
    this.cfg     = cfg;
    this.onEnd   = onEnd;    // callback({score, won, wp_hit, total_wp, hz_hit, time})
    this._raf    = null;
    this._then   = null;

    // Derived scale
    this.scaleX = canvas.width  / cfg.world.w;
    this.scaleY = canvas.height / cfg.world.h;

    // Vessel state
    const s = cfg.start;
    this.v = {
      x:       s.x,
      y:       s.y,
      heading: s.heading,     // degrees, 0 = north, 90 = east
      speed:   0,
      maxSpd:  cfg.vessel.max_speed,
      turnRate: cfg.vessel.turn_rate,
    };

    // Waypoints & hazards (copies)
    this.waypoints = cfg.waypoints.map((w, i) => ({ ...w, done: false, idx: i }));
    this.hazards   = cfg.hazards.map(h => ({ ...h, hit: false, flash: 0 }));
    this.nextWP    = 0;

    // Scoring
    this.hzHits  = 0;
    this.elapsed = 0;
    this.ended   = false;

    // Keys
    this.keys = new Set();
    this._onKey = e => {
      if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',
           'w','a','s','d','W','A','S','D'].includes(e.key)) {
        e.preventDefault();
        e.type === 'keydown' ? this.keys.add(e.key) : this.keys.delete(e.key);
      }
    };
    window.addEventListener('keydown', this._onKey);
    window.addEventListener('keyup',   this._onKey);

    // Trail
    this.trail = [];

    // Particle pool for hazard hits
    this.particles = [];
  }

  start() {
    if (this._raf !== null) return; // already running
    this._then = performance.now();
    this._tick = this._tick.bind(this);
    this._raf  = requestAnimationFrame(this._tick);
  }

  destroy() {
    if (this._raf !== null) cancelAnimationFrame(this._raf);
    window.removeEventListener('keydown', this._onKey);
    window.removeEventListener('keyup',   this._onKey);
    // clear transient state
    this.trail = [];
    this.particles = [];
    this._raf = null;
  }

  // ── Control helpers (called by on-screen buttons) ─────────────────────────
  pressKey(k)   { this.keys.add(k); }
  releaseKey(k) { this.keys.delete(k); }

  _tick(now) {
    if (this.ended) return;
    const dt = Math.min((now - this._then) / 1000, 0.1);
    this._then = now;
    this.elapsed += dt;

    if (this.elapsed >= this.cfg.time_limit) {
      this._endGame(false);
      return;
    }

    this._update(dt);
    this._draw();
    this._raf = requestAnimationFrame(this._tick);
  }

  _update(dt) {
    const v = this.v;
    const keys = this.keys;

    // Steering
    const left  = keys.has('ArrowLeft')  || keys.has('a') || keys.has('A');
    const right = keys.has('ArrowRight') || keys.has('d') || keys.has('D');
    const fwd   = keys.has('ArrowUp')    || keys.has('w') || keys.has('W');
    const back  = keys.has('ArrowDown')  || keys.has('s') || keys.has('S');

    if (left)  v.heading = (v.heading - v.turnRate * dt + 360) % 360;
    if (right) v.heading = (v.heading + v.turnRate * dt) % 360;

    // Throttle with drag
    if (fwd)       v.speed = Math.min(v.speed + 5  * dt, v.maxSpd);
    else if (back) v.speed = Math.max(v.speed - 7  * dt, 0);
    else           v.speed = Math.max(v.speed - 1.8 * dt, 0);

    // Movement: heading 0=north ↑, 90=east →
    const rad = (v.heading - 90) * (Math.PI / 180);
    v.x += Math.cos(rad) * v.speed * dt * 55 + this.cfg.current.x;
    v.y += Math.sin(rad) * v.speed * dt * 55 + this.cfg.current.y;

    // Clamp to world
    v.x = Math.max(0, Math.min(v.x, this.cfg.world.w));
    v.y = Math.max(0, Math.min(v.y, this.cfg.world.h));

    // Trail
    if (v.speed > 0.3) {
      this.trail.push({ x: v.x, y: v.y, age: 0 });
      if (this.trail.length > 120) this.trail.shift();
    }
    this.trail.forEach(p => p.age += dt);

    // Waypoint collection
    const wp = this.waypoints[this.nextWP];
    if (wp && !wp.done) {
      // Ensure waypoint radius is valid
      const wr = (typeof wp.r === 'number' && wp.r > 0) ? wp.r : 8;
      if (Math.hypot(v.x - wp.x, v.y - wp.y) < wr) {
        wp.done = true;
        this.nextWP++;
        if (this.nextWP >= this.waypoints.length) {
          this._endGame(true);
          return;
        }
      }
    }

    // Hazard collision
    for (const h of this.hazards) {
      const hr = (typeof h.r === 'number' && h.r > 0) ? h.r : 12;
      if (!h.hit && Math.hypot(v.x - h.x, v.y - h.y) < hr) {
        h.hit   = true;
        h.flash = 1.2;
        this.hzHits++;
        this._spawnParticles(v.x, v.y);
        // Bounce back
        v.x -= Math.cos(rad) * 30;
        v.y -= Math.sin(rad) * 30;
        v.speed *= 0.3;
      }
      if (h.flash > 0) h.flash = Math.max(0, h.flash - dt * 3);
    }

    // Particles
    this.particles.forEach(p => {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life -= dt * 1.5;
    });
    this.particles = this.particles.filter(p => p.life > 0);
  }

  _spawnParticles(x, y) {
    for (let i = 0; i < 12; i++) {
      const ang = Math.random() * Math.PI * 2;
      const spd = 20 + Math.random() * 60;
      this.particles.push({
        x, y,
        vx: Math.cos(ang) * spd,
        vy: Math.sin(ang) * spd,
        life: 1,
        r: 1 + Math.random() * 3,
      });
    }
  }

  _draw() {
    const ctx = this.ctx;
    const W   = this.canvas.width;
    const H   = this.canvas.height;
    const sx  = this.scaleX;
    const sy  = this.scaleY;
    const cw  = this.cfg.world.w;
    const ch  = this.cfg.world.h;

    // ── Ocean background ──────────────────────────────────────────────
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#061020');
    bg.addColorStop(1, '#0A1D33');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // ── Chart grid ────────────────────────────────────────────────────
    ctx.save();
    ctx.strokeStyle = 'rgba(46,142,247,0.07)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= cw; x += 200) {
      ctx.beginPath();
      ctx.moveTo(x * sx, 0); ctx.lineTo(x * sx, H); ctx.stroke();
    }
    for (let y = 0; y <= ch; y += 200) {
      ctx.beginPath();
      ctx.moveTo(0, y * sy); ctx.lineTo(W, y * sy); ctx.stroke();
    }
    ctx.restore();

    // ── Current field arrows ──────────────────────────────────────────
    const cu = this.cfg.current;
    const cuLen = Math.hypot(cu.x, cu.y);
    if (cuLen > 0.01) {
      ctx.save();
      ctx.globalAlpha = 0.18;
      ctx.strokeStyle = '#39D5C8';
      ctx.fillStyle   = '#39D5C8';
      ctx.lineWidth   = 1;
      const spacing = 160;
      for (let gx = spacing / 2; gx < cw; gx += spacing) {
        for (let gy = spacing / 2; gy < ch; gy += spacing) {
          this._arrow(ctx, gx * sx, gy * sy,
            (gx + cu.x * 70) * sx, (gy + cu.y * 70) * sy, 6);
        }
      }
      ctx.restore();
    }

    // ── Trail ─────────────────────────────────────────────────────────
    if (this.trail.length > 1) {
      ctx.save();
      for (let i = 1; i < this.trail.length; i++) {
        const a = Math.max(0, 0.6 - this.trail[i].age * 0.5) * 0.5;
        ctx.strokeStyle = `rgba(57,213,200,${a})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(this.trail[i - 1].x * sx, this.trail[i - 1].y * sy);
        ctx.lineTo(this.trail[i].x * sx,     this.trail[i].y * sy);
        ctx.stroke();
      }
      ctx.restore();
    }

    // ── Hazards ───────────────────────────────────────────────────────
    for (const h of this.hazards) {
      ctx.save();
      const base = h.hit ? 0.2 : 0.45;
      const extra = h.flash * 0.4;

      // Radial glow
      const rg = ctx.createRadialGradient(
        h.x * sx, h.y * sy, 0,
        h.x * sx, h.y * sy, h.r * sx
      );
      rg.addColorStop(0, `rgba(220,38,38,${base + extra})`);
      rg.addColorStop(1, 'rgba(220,38,38,0)');
      ctx.fillStyle = rg;
      ctx.beginPath();
      ctx.arc(h.x * sx, h.y * sy, h.r * sx, 0, Math.PI * 2);
      ctx.fill();

      // Border
      ctx.globalAlpha = h.hit ? 0.3 : (0.7 + h.flash * 0.3);
      ctx.strokeStyle = h.flash > 0.1 ? '#FF6666' : '#DC2626';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(h.x * sx, h.y * sy, h.r * sx, 0, Math.PI * 2);
      ctx.stroke();

      // Label
      ctx.globalAlpha = h.hit ? 0.35 : 0.9;
      ctx.fillStyle = '#FCA5A5';
      ctx.font = `${Math.round(11 * Math.max(sx, sy))}px Inter,sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText('⚠ ' + h.label, h.x * sx, h.y * sy - h.r * sy - 8);
      ctx.restore();
    }

    // ── Waypoints ─────────────────────────────────────────────────────
    for (let i = 0; i < this.waypoints.length; i++) {
      const wp = this.waypoints[i];
      ctx.save();

      if (wp.done) {
        // Collected marker
        ctx.globalAlpha = 0.25;
        ctx.fillStyle = '#39D5C8';
        ctx.beginPath();
        ctx.arc(wp.x * sx, wp.y * sy, wp.r * sx * 0.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 0.7;
        ctx.fillStyle = '#39D5C8';
        ctx.font = `bold ${Math.round(13 * Math.max(sx, sy))}px Inter,sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText('✓', wp.x * sx, wp.y * sy + 5 * sy);

      } else if (i === this.nextWP) {
        // Active — pulsing ring
        const pulse = 0.85 + 0.15 * Math.sin(performance.now() / 380);
        ctx.globalAlpha = 0.12 * pulse;
        ctx.fillStyle = '#2E8EF7';
        ctx.beginPath();
        ctx.arc(wp.x * sx, wp.y * sy, wp.r * sx * (1 + 0.12 * Math.sin(performance.now() / 380)), 0, Math.PI * 2);
        ctx.fill();

        ctx.globalAlpha = 0.9;
        ctx.strokeStyle = '#5BA7F9';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(wp.x * sx, wp.y * sy, wp.r * sx, 0, Math.PI * 2);
        ctx.stroke();

        // Label
        ctx.fillStyle = '#93C5FD';
        ctx.font = `bold ${Math.round(12 * Math.max(sx, sy))}px Inter,sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(wp.label, wp.x * sx, wp.y * sy - wp.r * sy - 9);
        ctx.fillStyle = '#2E8EF7';
        ctx.font = `${Math.round(10 * Math.max(sx, sy))}px Inter,sans-serif`;
        ctx.fillText(`WP ${i + 1}/${this.waypoints.length}`, wp.x * sx, wp.y * sy + 4 * sy);

      } else if (i > this.nextWP) {
        // Future — dashed outline
        ctx.globalAlpha = 0.35;
        ctx.strokeStyle = '#39D5C8';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.arc(wp.x * sx, wp.y * sy, wp.r * sx, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = '#39D5C8';
        ctx.font = `${Math.round(10 * Math.max(sx, sy))}px Inter,sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(wp.label, wp.x * sx, wp.y * sy - wp.r * sy - 7);
      }
      ctx.restore();
    }

    // ── Particles ─────────────────────────────────────────────────────
    ctx.save();
    for (const p of this.particles) {
      ctx.globalAlpha = p.life * 0.9;
      ctx.fillStyle = '#FCA5A5';
      ctx.beginPath();
      ctx.arc(p.x * sx, p.y * sy, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    // ── Vessel ────────────────────────────────────────────────────────
    const vx  = this.v.x * sx;
    const vy  = this.v.y * sy;
    const ang = (this.v.heading - 90) * (Math.PI / 180);
    const sz  = Math.max(sx, sy) * 16;

    ctx.save();
    ctx.translate(vx, vy);
    ctx.rotate(ang + Math.PI / 2);

    // Hull gradient
    const hg = ctx.createLinearGradient(0, -sz, 0, sz * 0.6);
    hg.addColorStop(0, '#60A5FA');
    hg.addColorStop(1, '#1D4ED8');
    ctx.fillStyle = hg;
    ctx.beginPath();
    ctx.moveTo(0,        -sz);
    ctx.lineTo(sz * 0.48,  sz * 0.55);
    ctx.lineTo(0,          sz * 0.25);
    ctx.lineTo(-sz * 0.48, sz * 0.55);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = 'rgba(147,197,253,0.8)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Bow light
    ctx.fillStyle = '#FDE68A';
    ctx.beginPath();
    ctx.arc(0, -sz * 0.9, sz * 0.1, 0, Math.PI * 2);
    ctx.fill();

    // Wake
    if (this.v.speed > 0.5) {
      const wakeAlpha = Math.min(this.v.speed / this.v.maxSpd * 0.5, 0.4);
      ctx.globalAlpha = wakeAlpha;
      ctx.strokeStyle = '#93C5FD';
      ctx.lineWidth   = 1;
      for (let i = 1; i <= 3; i++) {
        ctx.beginPath();
        ctx.arc(0, sz * 0.4 + i * 9, i * 5, 0, Math.PI);
        ctx.stroke();
      }
    }
    ctx.restore();

    // Heading line
    ctx.save();
    ctx.globalAlpha = 0.35;
    ctx.strokeStyle = '#2E8EF7';
    ctx.lineWidth   = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(vx, vy);
    ctx.lineTo(vx + Math.cos(ang) * 70, vy + Math.sin(ang) * 70);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // ── HUD ───────────────────────────────────────────────────────────
    this._drawHUD(ctx, W, H);
  }

  _drawHUD(ctx, W, H) {
    const timeLeft = Math.max(0, this.cfg.time_limit - this.elapsed);
    const wpDone   = this.waypoints.filter(w => w.done).length;
    const urgent   = timeLeft < 30;

    ctx.save();

    // Top-left: timer
    ctx.fillStyle = 'rgba(10,14,26,0.75)';
    ctx.beginPath();
    this._roundRect(ctx, 12, 12, 130, 58, 10);
    ctx.fill();
    ctx.fillStyle = urgent ? '#FCA5A5' : '#93C5FD';
    ctx.font = 'bold 11px Inter,sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('TIME REMAINING', 22, 28);
    ctx.font = `bold ${urgent ? 22 : 20}px Inter,sans-serif`;
    ctx.fillStyle = urgent ? '#F87171' : '#60A5FA';
    const m = Math.floor(timeLeft / 60);
    const s = Math.floor(timeLeft % 60);
    ctx.fillText(`${m}:${s.toString().padStart(2, '0')}`, 22, 55);

    // Top-center: waypoints
    ctx.fillStyle = 'rgba(10,14,26,0.75)';
    ctx.beginPath();
    const wcX = W / 2 - 70;
    this._roundRect(ctx, wcX, 12, 140, 58, 10);
    ctx.fill();
    ctx.fillStyle = '#6EE7B7';
    ctx.font = 'bold 11px Inter,sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('WAYPOINTS', W / 2, 28);
    ctx.font = 'bold 20px Inter,sans-serif';
    ctx.fillStyle = '#34D399';
    ctx.fillText(`${wpDone} / ${this.waypoints.length}`, W / 2, 55);

    // Top-right: speed & heading
    ctx.fillStyle = 'rgba(10,14,26,0.75)';
    ctx.beginPath();
    this._roundRect(ctx, W - 142, 12, 130, 58, 10);
    ctx.fill();
    ctx.fillStyle = '#FCD34D';
    ctx.font = 'bold 11px Inter,sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('HDG  SPD', W - 22, 28);
    ctx.font = 'bold 16px Inter,sans-serif';
    ctx.fillStyle = '#FDE68A';
    const hdg = Math.round(this.v.heading).toString().padStart(3, '0');
    const spd = this.v.speed.toFixed(1);
    ctx.fillText(`${hdg}°  ${spd}kn`, W - 22, 52);

    // Hazard hit warning
    if (this.hzHits > 0) {
      ctx.fillStyle = 'rgba(127,29,29,0.7)';
      ctx.beginPath();
      this._roundRect(ctx, W - 142, 80, 130, 36, 8);
      ctx.fill();
      ctx.fillStyle = '#FCA5A5';
      ctx.font = 'bold 12px Inter,sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`⚠ ${this.hzHits} collision${this.hzHits > 1 ? 's' : ''}`, W - 22, 103);
    }

    ctx.restore();
  }

  _arrow(ctx, x1, y1, x2, y2, hs) {
    const dx = x2 - x1, dy = y2 - y1;
    const a  = Math.atan2(dy, dx);
    ctx.beginPath();
    ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
    ctx.lineTo(x2 - hs * Math.cos(a - Math.PI / 6), y2 - hs * Math.sin(a - Math.PI / 6));
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - hs * Math.cos(a + Math.PI / 6), y2 - hs * Math.sin(a + Math.PI / 6));
    ctx.stroke();
  }

  _roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  _endGame(won) {
    if (this.ended) return;
    this.ended = true;
    cancelAnimationFrame(this._raf);

    const wpHit    = this.waypoints.filter(w => w.done).length;
    const wpTotal  = this.waypoints.length;
    const wpFrac   = wpHit / wpTotal;
    const penalty  = Math.min(this.hzHits * 12, 30);
    const timePar  = this.cfg.time_par;
    const timeBonus = (won && this.elapsed <= timePar)
      ? Math.round(25 * (1 - this.elapsed / timePar))
      : 0;
    const score = Math.max(0, Math.round(wpFrac * 75 - penalty + timeBonus));

    this._draw();     // one final frame
    this.onEnd({
      score,
      won,
      wp_hit:    wpHit,
      total_wp:  wpTotal,
      hz_hit:    this.hzHits,
      time_taken: Math.round(this.elapsed),
    });
  }
}
