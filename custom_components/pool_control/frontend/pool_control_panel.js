/**
 * Pool Control — Panel custom pour Home Assistant
 *
 * Synoptique réaliste du local technique et assistant de lavage du filtre.
 * Web Component vanilla JS — pas de build, pas de dépendances.
 * Lit les entités via hass.states / hass.entities, écrit via hass.callService().
 */

// Alerte d'incohérence relais / consommation
const POWER_THRESHOLD_W = 5;
const MISMATCH_DELAY_MS = 60 * 1000;
// Nouvelle recherche d'un capteur de puissance introuvable
const POWER_LOOKUP_RETRY_MS = 60 * 1000;

const VALVE_ANGLES = {
  filtration: 0, lavage: 60, 'rinçage': 120, 'égout': 180, circulation: 240, 'fermé': 300,
};
const VALVE_POSITIONS = ['filtration', 'lavage', 'rinçage', 'égout', 'circulation', 'fermé'];

// Pipes : aspiration, refoulement, sortie filtre, by-pass / PAC, retour, surpresseur
const PIPES = 'M224 104V250M128 196V250H256M300 232V100H414M432 82V40H492M450 100H640V430H26V120H40M508 100V160M596 160V100M90 430V366M70 334V196';

class PoolControlPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._rendered = false;
    this._cfg = {};
    this._powerCache = {};
    this._entitiesRef = null;
    this._lastBackwashStep = null;
    this._backwashOutcome = null;
    this._armTimer = null;
    this._tick = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._cfg = (this.panel && this.panel.config) || {};
      this._render();
      this._rendered = true;
    }
    this._update();
  }

  get hass() { return this._hass; }
  set narrow(v) { this._narrow = v; this.toggleAttribute('narrow', !!v); }
  set route(v) { this._route = v; }
  set panel(v) { this._panel = v; }
  get panel() { return this._panel; }

  connectedCallback() {
    // Réévalue les alertes temporisées et la position « maintenant » sans attendre un changement d'état
    this._tick = setInterval(() => this._update(), 5000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
    clearTimeout(this._armTimer);
  }

  /* ---------------------------------------------------------------- données */

  _prefix() { return this._cfg.instance_prefix || 'pool_control'; }
  _lang() { return (this._hass && ((this._hass.locale && this._hass.locale.language) || this._hass.language)) || 'fr'; }

  _state(id) {
    if (!id || !this._hass || !this._hass.states[id]) return null;
    return this._hass.states[id];
  }

  _stateText(id, fallback = '') {
    const s = this._state(id);
    return s ? s.state : fallback;
  }

  _isOn(id) { return this._stateText(id) === 'on'; }

  _friendlyName(id, fallback) {
    const s = this._state(id);
    return (s && s.attributes && s.attributes.friendly_name) || fallback;
  }

  _fmtTemp(id) {
    const s = this._state(id);
    const v = s ? parseFloat(s.state) : NaN;
    if (isNaN(v)) return '—';
    return `${v.toLocaleString(this._lang(), { minimumFractionDigits: 1, maximumFractionDigits: 1 })} °C`;
  }

  _watts(id) {
    const s = this._state(id);
    if (!s) return null;
    let v = parseFloat(s.state);
    if (isNaN(v)) return null;
    const unit = s.attributes && s.attributes.unit_of_measurement;
    if (unit === 'kW') v *= 1000;
    return v;
  }

  _fmtWatts(v) {
    if (v === null || v === undefined) return '';
    if (v >= 1000) return `${(v / 1000).toLocaleString(this._lang(), { maximumFractionDigits: 2 })} kW`;
    return `${Math.round(v).toLocaleString(this._lang())} W`;
  }

  // Capteur de puissance porté par le même appareil que l'entité (ex. voie d'un Shelly Pro 4PM)
  _powerSensorFor(entityId) {
    if (!entityId || !this._hass) return null;
    const entities = this._hass.entities;
    if (entities !== this._entitiesRef) {
      this._entitiesRef = entities;
      this._powerCache = {};
    }
    const cached = this._powerCache[entityId];
    if (cached && (cached.id || Date.now() - cached.at < POWER_LOOKUP_RETRY_MS)) return cached.id;

    let found = null;
    const reg = entities && entities[entityId];
    if (reg && reg.device_id) {
      for (const e of Object.values(entities)) {
        if (e.device_id !== reg.device_id || !e.entity_id.startsWith('sensor.')) continue;
        const st = this._hass.states[e.entity_id];
        if (st && st.attributes && st.attributes.device_class === 'power') { found = e.entity_id; break; }
      }
    }
    this._powerCache[entityId] = { id: found, at: Date.now() };
    return found;
  }

  _isHeatPumpRunning() {
    const id = this._cfg.heat_pump_entity;
    const st = this._state(id);
    if (!st) return false;

    // Pour une entité climate, le state correspond au hvac_mode
    // (heat / cool / off) et reste à "heat" même quand la PAC est idle.
    // On lit donc en priorité attributes.hvac_action.
    if (id.startsWith('climate.')) {
      const action = (st.attributes && st.attributes.hvac_action) || '';
      if (action) return /^(heating|cooling|drying|fan)$/i.test(action);
      return !/^(off|unknown|unavailable)$/i.test(st.state);
    }
    return /^on$/i.test(st.state);
  }

  // Relais activé mais moins de 5 W, ou relais éteint mais plus de 5 W, depuis au moins 60 s
  _mismatch(entityId, powerId, on, onlyWhenOn) {
    if (!entityId || !powerId) return null;
    const relay = this._state(entityId);
    const power = this._state(powerId);
    const w = this._watts(powerId);
    if (!relay || !power || w === null || /^(unknown|unavailable)$/.test(relay.state)) return null;

    let kind = null;
    if (on && w < POWER_THRESHOLD_W) kind = 'nopower';
    else if (!onlyWhenOn && !on && w > POWER_THRESHOLD_W) kind = 'unexpected';
    if (!kind) return null;

    const relayChanged = entityId.startsWith('climate.') ? relay.last_updated : relay.last_changed;
    const since = Math.max(Date.parse(relayChanged) || 0, Date.parse(power.last_changed) || 0);
    return Date.now() - since >= MISMATCH_DELAY_MS ? kind : null;
  }

  _controlMode() {
    const raw = this._stateText(`sensor.${this._prefix()}_control_status`);
    const lower = raw.toLowerCase();
    let mode = 'inconnu';
    if (lower.includes('inactif')) mode = 'inactif';
    else if (lower.includes('actif')) mode = 'actif';
    else if (lower.includes('auto')) mode = 'auto';
    const season = lower.includes('hivernage') ? 'hivernage' : 'saison';
    return { mode, season, raw };
  }

  // Étape de l'assistant (lavage.py) : 0 arrêté, 1 position lavage, 2 lavage,
  // 3 position rinçage, 4 rinçage, 5 position filtration
  _backwash() {
    const raw = this._stateText(`sensor.${this._prefix()}_backwash_status`);
    const s = raw.toLowerCase();
    let step = 0;
    if (s.includes('position lavage')) step = 1;
    else if (s.includes('position rin')) step = 3;
    else if (s.includes('position filtration')) step = 5;
    else if (s.startsWith('lavage')) step = 2;
    else if (s.startsWith('rin')) step = 4;
    const m = s.match(/(\d{1,3}):(\d{2})/);
    const remain = m ? parseInt(m[1], 10) * 60 + parseInt(m[2], 10) : null;
    return { step, remain, raw };
  }

  _schedule() {
    const raw = this._stateText(`sensor.${this._prefix()}_filtration_schedule`);
    const ranges = [];
    const re = /(\d{2}):(\d{2})-(\d{2}):(\d{2})/g;
    let m;
    while ((m = re.exec(raw))) {
      ranges.push([parseInt(m[1], 10) * 60 + parseInt(m[2], 10), parseInt(m[3], 10) * 60 + parseInt(m[4], 10), `${m[1]}:${m[2]}`, `${m[3]}:${m[4]}`]);
    }
    const t = raw.match(/:\s*(-?[\d.]+)\s*°C/);
    const temp = t ? parseFloat(t[1]).toLocaleString(this._lang(), { maximumFractionDigits: 1 }) : null;
    return { raw, ranges, temp, winter: raw.trim().startsWith('*') };
  }

  // Minutes écoulées dans la journée, dans le fuseau de Home Assistant
  _nowMinutes() {
    const tz = this._hass && this._hass.config && this._hass.config.time_zone;
    try {
      const parts = new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
      const get = (type) => parseInt(parts.find((p) => p.type === type).value, 10);
      return get('hour') * 60 + get('minute');
    } catch (e) {
      const d = new Date();
      return d.getHours() * 60 + d.getMinutes();
    }
  }

  _fmtClock(minutes) {
    return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
  }

  /* -------------------------------------------------------------- actions */

  _callService(domain, service, target) {
    if (!this._hass) return;
    return this._hass.callService(domain, service, { entity_id: target });
  }

  _press(key) {
    return this._callService('button', 'press', `button.${this._prefix()}_${key}`);
  }

  _moreInfo(entityId) {
    if (!entityId) return;
    this.dispatchEvent(new CustomEvent('hass-more-info', { detail: { entityId }, bubbles: true, composed: true }));
  }

  // Action sensible : un premier clic arme le bouton, un second dans les 4 s confirme
  _armed(btn, confirmLabel, action) {
    if (btn.dataset.armed) {
      this._disarm(btn);
      action();
      return;
    }
    this.shadowRoot.querySelectorAll('[data-armed]').forEach((b) => this._disarm(b));
    btn.dataset.armed = '1';
    btn.dataset.label = btn.textContent;
    btn.textContent = confirmLabel;
    btn.classList.add('armed');
    this._armTimer = setTimeout(() => this._disarm(btn), 4000);
  }

  _disarm(btn) {
    clearTimeout(this._armTimer);
    if (!btn.dataset.armed) return;
    btn.textContent = btn.dataset.label;
    delete btn.dataset.armed;
    delete btn.dataset.label;
    btn.classList.remove('armed');
  }

  /* --------------------------------------------------------------- rendu */

  _render() {
    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>
      <div class="toolbar">
        <button class="menu-btn" id="menu-btn" aria-label="Menu">
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M3 6h18v2H3zm0 5h18v2H3zm0 5h18v2H3z"/></svg>
        </button>
        <h1 id="title">Pool Control</h1>
      </div>
      <div class="wrap">
        <div class="status">
          <div class="chips">
            <span class="chip" id="chip-mode">—</span>
            <span class="chip" id="chip-state">—</span>
          </div>
          <div class="chips">
            <button class="chip temp" id="temp-water">Eau —</button>
            <button class="chip temp" id="temp-air">Air —</button>
          </div>
        </div>

        <div class="grid">
          <section class="card panel" id="panel">
            <div id="view-syn">${this._synopticMarkup()}</div>
            <div id="view-bw" hidden>${this._backwashMarkup()}</div>
          </section>

          <aside class="side">
            <div class="card">
              <h2>Planning du jour</h2>
              <div class="track" id="plan-track"><div id="plan-segs"></div><div class="now" id="plan-now"></div></div>
              <div class="ticks"><span>00</span><span>06</span><span>12</span><span>18</span><span>24</span></div>
              <div class="muted" id="plan-text">—</div>
            </div>
            <div class="card">
              <h2>Pilotage</h2>
              <div class="row">
                <button class="btn" id="btn-auto">Auto</button>
                <button class="btn" id="btn-active">Actif</button>
                <button class="btn" id="btn-inactive">Inactif</button>
              </div>
              <div class="row gap-top">
                <button class="btn" id="btn-season">Saison</button>
                <button class="btn" id="btn-winter">Hivernage</button>
                <button class="btn" id="btn-reset">Recalculer</button>
              </div>
            </div>
            <div class="card">
              <h2>Lavage du filtre</h2>
              <div class="line" id="bw-side-line">
                <span id="bw-side">—</span>
                <button class="btn primary" id="bw-start">Démarrer le lavage</button>
              </div>
            </div>
            <div class="card">
              <h2>Surpresseur</h2>
              <div class="line">
                <span id="bo-txt">—</span>
                <span class="row">
                  <button class="btn" id="btn-booster">Lancer</button>
                  <button class="btn warn" id="btn-booster-stop">Arrêter</button>
                </span>
              </div>
            </div>
          </aside>
        </div>
      </div>
    `;

    const $ = (id) => this.shadowRoot.getElementById(id);
    const c = this._cfg;

    $('menu-btn').addEventListener('click', () => {
      this.dispatchEvent(new CustomEvent('hass-toggle-menu', { bubbles: true, composed: true }));
    });
    $('temp-water').addEventListener('click', () => this._moreInfo(c.water_entity));
    $('temp-air').addEventListener('click', () => this._moreInfo(c.air_entity));

    const targets = {
      pool: () => c.water_entity,
      pump: () => c.filtration_entity,
      filter: () => `sensor.${this._prefix()}_backwash_status`,
      pac: () => c.heat_pump_entity,
      cl: () => c.treatment_entity,
      ph: () => c.treatment_2_entity,
      bo: () => c.booster_entity,
    };
    this.shadowRoot.querySelectorAll('[data-eq]').forEach((g) => {
      const open = () => this._moreInfo(targets[g.dataset.eq]());
      g.addEventListener('click', open);
      g.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); }
      });
    });

    $('btn-auto').addEventListener('click', () => this._press('auto'));
    $('btn-active').addEventListener('click', () => this._press('active'));
    $('btn-inactive').addEventListener('click', (ev) => this._armed(ev.currentTarget, 'Confirmer', () => this._press('inactive')));
    $('btn-season').addEventListener('click', () => this._press('season'));
    $('btn-winter').addEventListener('click', (ev) => this._armed(ev.currentTarget, 'Confirmer', () => this._press('winter')));
    $('btn-reset').addEventListener('click', () => this._press('reset'));

    $('bw-start').addEventListener('click', () => {
      this._backwashOutcome = null;
      this._press('backwash');
      $('panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    $('bw-main').addEventListener('click', () => this._press('backwash'));
    $('bw-stop').addEventListener('click', (ev) => this._armed(ev.currentTarget, "Confirmer l'annulation", () => this._press('stop')));

    $('btn-booster').addEventListener('click', () => this._press('booster'));
    $('btn-booster-stop').addEventListener('click', () => this._press('stop'));
  }

  _update() {
    if (!this._rendered || !this._hass) return;
    const $ = (id) => this.shadowRoot.getElementById(id);
    const c = this._cfg;

    this.toggleAttribute('dark', !!(this._hass.themes && this._hass.themes.darkMode));
    $('title').textContent = (this.panel && this.panel.title) || 'Pool Control';

    /* Températures */
    const water = this._fmtTemp(c.water_entity);
    $('temp-water').textContent = `Eau ${water}`;
    $('temp-air').textContent = `Air ${this._fmtTemp(c.air_entity)}`;
    $('t-water').textContent = water;

    /* Équipements */
    const pacConfigured = !!c.heat_pump_entity;
    const eq = {
      pump: { entity: c.filtration_entity, name: 'Pompe' },
      cl: { entity: c.treatment_entity, name: this._friendlyName(c.treatment_entity, 'Traitement') },
      ph: { entity: c.treatment_2_entity, name: this._friendlyName(c.treatment_2_entity, 'Traitement 2') },
      bo: { entity: c.booster_entity, name: 'Surpresseur' },
      pac: { entity: c.heat_pump_entity, name: 'PAC' },
    };
    for (const [k, e] of Object.entries(eq)) {
      e.on = k === 'pac' ? this._isHeatPumpRunning() : this._isOn(e.entity);
      e.power = k === 'pac' ? (c.heat_pump_power_entity || this._powerSensorFor(e.entity)) : this._powerSensorFor(e.entity);
      e.watts = e.power ? this._watts(e.power) : null;
      e.alert = this._mismatch(e.entity, e.power, e.on, k === 'pac');
    }

    const ctrl = this._controlMode();
    const bw = this._backwash();
    const sched = this._schedule();

    /* Fin ou annulation de l'assistant, constatée pendant que le panneau est ouvert */
    if (this._lastBackwashStep !== null && this._lastBackwashStep > 0 && bw.step === 0) {
      this._backwashOutcome = this._lastBackwashStep === 5
        ? { kind: 'done', at: this._fmtClock(this._nowMinutes()) }
        : { kind: 'cancelled' };
    }
    this._lastBackwashStep = bw.step;

    /* Chips d'état */
    $('chip-mode').textContent = ctrl.raw
      ? `${ctrl.mode === 'inconnu' ? ctrl.raw : ctrl.mode.charAt(0).toUpperCase() + ctrl.mode.slice(1)} · ${ctrl.season}`
      : '—';
    const alerted = Object.values(eq).find((e) => e.alert);
    const chip = $('chip-state');
    let state = { text: "À l'arrêt", tone: '' };
    if (bw.step > 0) state = { text: 'Lavage du filtre en cours', tone: 'warn' };
    else if (alerted) state = { text: alerted.alert === 'nopower' ? `Défaut : ${alerted.name} activé mais sans consommation` : `Défaut : ${alerted.name} éteint mais consomme`, tone: 'warn' };
    else if (ctrl.mode === 'inactif') state = { text: 'Contrôle désactivé', tone: '' };
    else if (eq.pump.on) state = { text: eq.bo.on ? 'En filtration · surpresseur' : (pacConfigured && eq.pac.on ? 'En filtration · chauffe' : 'En filtration'), tone: 'run' };
    chip.textContent = state.text;
    chip.className = `chip${state.tone ? ` ${state.tone}` : ''}`;

    /* Vues */
    $('view-syn').hidden = bw.step > 0;
    $('view-bw').hidden = bw.step === 0;

    if (bw.step === 0) this._updateSynoptic(eq, pacConfigured);
    else this._updateBackwash(bw);

    /* Planning */
    const segs = $('plan-segs');
    segs.textContent = '';
    for (const [a, b] of sched.ranges) {
      const parts = b >= a ? [[a, b]] : [[a, 1440], [0, b]];
      for (const [s, e] of parts) {
        const d = document.createElement('div');
        d.className = 'seg';
        d.style.left = `${(s / 1440) * 100}%`;
        d.style.width = `${((e - s) / 1440) * 100}%`;
        segs.appendChild(d);
      }
    }
    $('plan-now').style.left = `${(this._nowMinutes() / 1440) * 100}%`;
    const time = this._stateText(`sensor.${this._prefix()}_filtration_time`);
    const tm = time.match(/^(\d{2}):(\d{2})$/);
    const bits = [];
    if (sched.ranges.length) bits.push(`${sched.winter ? 'Hivernage · ' : ''}${sched.ranges.map((r) => `${r[2]} – ${r[3]}`).join(', ')}`);
    if (tm) bits.push(`${parseInt(tm[1], 10)} h ${tm[2]} de filtration`);
    if (sched.temp) bits.push(`calcul sur ${sched.temp} °C`);
    $('plan-text').textContent = bits.length ? bits.join(' · ') : 'Planning disponible au prochain calcul';

    /* Pilotage */
    $('btn-auto').classList.toggle('on', ctrl.mode === 'auto');
    $('btn-active').classList.toggle('on', ctrl.mode === 'actif');
    $('btn-inactive').classList.toggle('on', ctrl.mode === 'inactif');
    $('btn-season').classList.toggle('on', ctrl.season === 'saison');
    $('btn-winter').classList.toggle('on', ctrl.season === 'hivernage');

    /* Lavage (colonne) */
    const bwStart = $('bw-start');
    bwStart.disabled = bw.step > 0 || eq.bo.on;
    bwStart.textContent = bw.step > 0 ? 'En cours' : 'Démarrer le lavage';
    const outcome = this._backwashOutcome;
    $('bw-side-line').classList.toggle('warn', bw.step === 0 && !!outcome && outcome.kind === 'cancelled');
    let side = `Lavage ${c.backwash_duration ?? 2} min, puis rinçage ${c.rinse_duration ?? 2} min`;
    if (bw.step > 0) side = `Étape ${bw.step} sur 5`;
    else if (eq.bo.on) side = "Arrêtez d'abord le surpresseur";
    else if (outcome && outcome.kind === 'cancelled') side = 'Annulé : vérifiez que la manette est sur filtration';
    else if (outcome && outcome.kind === 'done') side = `Dernier lavage terminé à ${outcome.at}`;
    $('bw-side').textContent = side;

    /* Surpresseur */
    const booster = this._stateText(`sensor.${this._prefix()}_booster_status`, '—');
    const boActive = /actif/i.test(booster);
    $('bo-txt').textContent = booster + (eq.bo.watts !== null && eq.bo.on ? ` · ${this._fmtWatts(eq.bo.watts)}` : '');
    $('btn-booster').disabled = boActive || bw.step > 0;
    $('btn-booster-stop').disabled = !boActive;
  }

  _updateSynoptic(eq, pacConfigured) {
    const $ = (id) => this.shadowRoot.getElementById(id);
    const pump = eq.pump.on;
    const pacRun = pacConfigured && eq.pac.on;

    const flows = [];
    if (pump) flows.push('asp', 'ref', 'main1', 'main2', pacRun ? 'pac' : 'byp');
    if (eq.bo.on) flows.push('balai');
    this.shadowRoot.querySelectorAll('.fl').forEach((p) => p.classList.toggle('on', flows.includes(p.dataset.k)));

    const ledColor = (e) => (e.alert ? '#EF9F27' : e.on ? '#1D9E75' : '#B4B2A9');
    $('led-pump').setAttribute('fill', ledColor(eq.pump));
    $('led-bo').setAttribute('fill', ledColor(eq.bo));
    $('w-pump').textContent = this._fmtWatts(eq.pump.watts);
    $('w-bo').textContent = this._fmtWatts(eq.bo.watts);

    for (const k of ['cl', 'ph']) {
      const e = eq[k];
      const g = $(`g-${k}`);
      const configured = !!e.entity;
      g.style.display = configured ? '' : 'none';
      $(`t-${k}`).style.display = configured ? '' : 'none';
      if (!configured) continue;
      $(`scr-${k}`).setAttribute('fill', e.alert ? '#EF9F27' : e.on ? '#1D9E75' : '#2B2B29');
      const w = this._fmtWatts(e.watts);
      $(`t-${k}`).textContent = w ? `${e.name} · ${w}` : e.name;
    }

    $('pac-g').classList.toggle('nocfg', !pacConfigured);
    $('pac-g').setAttribute('tabindex', pacConfigured ? '0' : '-1');
    $('fan').classList.toggle('spin', pacRun);
    $('pac-disp').textContent = !pacConfigured ? '--' : pacRun ? 'ON' : 'OFF';
    const pacW = this._fmtWatts(eq.pac.watts);
    $('t-pac').textContent = !pacConfigured ? 'Non configurée' : `${pacRun ? 'En chauffe' : 'Arrêt'}${pacW ? ` · ${pacW}` : ''}`;
    $('vh-byp').setAttribute('transform', pacRun ? 'rotate(90 552 100)' : '');
    $('vh-pin').setAttribute('transform', pacRun ? '' : 'rotate(90 508 128)');
    $('vh-pout').setAttribute('transform', pacRun ? '' : 'rotate(90 596 128)');

    for (const k of ['pump', 'bo', 'cl', 'ph', 'pac']) {
      $(`alert-${k}`).style.opacity = eq[k].alert ? '1' : '0';
    }
  }

  _updateBackwash(bw) {
    const $ = (id) => this.shadowRoot.getElementById(id);
    const c = this._cfg;
    const washMin = c.backwash_duration ?? 2;
    const rinseMin = c.rinse_duration ?? 2;
    const STEPS = {
      1: { run: false, valve: 'filtration', target: 'lavage', main: 'Vanne sur lavage : étape suivante' },
      2: { run: true, valve: 'lavage', total: washMin * 60, main: rinseMin ? 'Passer au rinçage' : 'Terminer le lavage', title: 'Lavage en cours', body: "L'eau remonte dans le sable et part à l'égout avec les impuretés." },
      3: { run: false, valve: 'lavage', target: 'rinçage', main: 'Vanne sur rinçage : étape suivante' },
      4: { run: true, valve: 'rinçage', total: (rinseMin || washMin) * 60, main: 'Terminer le rinçage', title: 'Rinçage en cours', body: "L'eau descend dans le sable vers l'égout pour le tasser." },
      5: { run: false, valve: 'rinçage', target: 'filtration', main: 'Vanne sur filtration : terminer' },
    };
    const st = STEPS[bw.step];
    const upper = { filtration: 'FILTRATION', lavage: 'LAVAGE', 'rinçage': 'RINÇAGE' };

    const rot = `rotate(${VALVE_ANGLES[st.valve] - 90} 150 125)`;
    $('dh').setAttribute('transform', rot);
    $('dh-hl').setAttribute('transform', rot);
    this.shadowRoot.querySelectorAll('.dl').forEach((l) => {
      l.classList.toggle('cur', l.dataset.p === st.valve && !st.target);
      l.classList.toggle('tgt', l.dataset.p === st.target);
    });
    VALVE_POSITIONS.forEach((p, i) => {
      $(`tick-${i}`).style.stroke = p === st.target ? 'var(--pc-warn)' : p === st.valve ? 'var(--pc-accent)' : 'var(--pc-line)';
    });

    $('bw-up').classList.toggle('on', st.run && st.valve === 'lavage');
    $('bw-down').classList.toggle('on', st.run && st.valve === 'rinçage');
    $('bw-out').classList.toggle('on', st.run);
    $('bw-dest').textContent = st.run ? 'Égout' : '—';
    $('bw-sand').textContent = st.run
      ? (st.valve === 'lavage' ? 'Le sable est soulevé et décolmaté' : 'Le sable se tasse')
      : 'Pompe arrêtée, eau immobile';

    this.shadowRoot.querySelectorAll('#steps li').forEach((li) => {
      const n = parseInt(li.dataset.s, 10);
      li.classList.toggle('done', n < bw.step);
      li.classList.toggle('cur', n === bw.step);
    });
    $('dur-l').textContent = `${washMin} min`;
    $('dur-r').textContent = rinseMin ? `${rinseMin} min` : 'désactivé';
    $('set-l').textContent = `${washMin} min`;
    $('set-r').textContent = rinseMin ? `${rinseMin} min` : 'désactivé (0 min)';

    $('bw-main').textContent = st.main;
    $('prog-w').hidden = !st.run;
    const instr = $('instr');
    instr.textContent = '';
    const strong = document.createElement('strong');
    const span = document.createElement('span');
    if (st.target) {
      strong.textContent = `Positionnez la vanne sur ${upper[st.target]}`;
      span.textContent = 'La pompe est arrêtée. Tournez la manette, puis appuyez sur le bouton.';
      $('bw-chip').textContent = `Action requise · étape ${bw.step} sur 5`;
    } else {
      const remain = bw.remain ?? st.total;
      const clock = `${String(Math.floor(remain / 60)).padStart(2, '0')}:${String(remain % 60).padStart(2, '0')}`;
      strong.textContent = `${st.title} · ${clock} restantes`;
      span.textContent = st.body;
      $('prog').style.width = `${Math.min(100, Math.max(0, 100 * (1 - remain / st.total)))}%`;
      $('bw-chip').textContent = `${bw.step === 2 ? 'Lavage' : 'Rinçage'} · étape ${bw.step} sur 5`;
    }
    instr.append(strong, span);
  }

  /* ------------------------------------------------------------ gabarits */

  _synopticMarkup() {
    return `
      <svg class="scene" viewBox="0 0 680 480" role="img">
        <title>Synoptique du local technique de la piscine</title>
        <defs>
          <linearGradient id="g-tank" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8E8C85"/><stop offset=".35" stop-color="#E9E7E0"/><stop offset=".7" stop-color="#C4C2BA"/><stop offset="1" stop-color="#83817A"/></linearGradient>
          <linearGradient id="g-motor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6A6963"/><stop offset=".3" stop-color="#C1BFB7"/><stop offset=".65" stop-color="#8A8982"/><stop offset="1" stop-color="#4B4A46"/></linearGradient>
          <linearGradient id="g-pot" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#A3A199"/><stop offset=".4" stop-color="#EFEDE6"/><stop offset="1" stop-color="#9A988F"/></linearGradient>
          <linearGradient id="g-water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A6CCF2"/><stop offset="1" stop-color="#3F86CB"/></linearGradient>
          <linearGradient id="g-pac" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FCFBF7"/><stop offset="1" stop-color="#D5D3CB"/></linearGradient>
          <radialGradient id="g-grille" cx=".4" cy=".35" r=".75"><stop offset="0" stop-color="#8F8D86"/><stop offset="1" stop-color="#3F3E3B"/></radialGradient>
          <radialGradient id="g-knob" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#8D8C87"/><stop offset="1" stop-color="#2B2B29"/></radialGradient>
          <radialGradient id="g-valve" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#A3A199"/><stop offset="1" stop-color="#3E3D3A"/></radialGradient>
          <linearGradient id="g-yellow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FCD994"/><stop offset="1" stop-color="#D5962A"/></linearGradient>
          <linearGradient id="g-blue" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ADD0F3"/><stop offset="1" stop-color="#4C8CCD"/></linearGradient>
          <linearGradient id="g-can" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C6C4BC"/><stop offset=".4" stop-color="#FFFFFF"/><stop offset="1" stop-color="#B9B7AF"/></linearGradient>
        </defs>

        <ellipse cx="308" cy="279" rx="62" ry="5" class="shadow"/>
        <ellipse cx="432" cy="310" rx="42" ry="5" class="shadow"/>
        <ellipse cx="552" cy="239" rx="66" ry="4" class="shadow"/>
        <ellipse cx="81" cy="369" rx="34" ry="4" class="shadow"/>
        <ellipse cx="426" cy="402" rx="16" ry="3" class="shadow"/>
        <ellipse cx="602" cy="402" rx="16" ry="3" class="shadow"/>

        <path class="pb" d="${PIPES}"/>
        <path class="pm" d="${PIPES}"/>
        <path class="pi" d="${PIPES}"/>
        <path class="fl" data-k="asp" d="M224 104V250M128 196V250H256"/>
        <path class="fl" data-k="ref" d="M300 232V100H414"/>
        <path class="fl" data-k="main1" d="M450 100H508"/>
        <path class="fl" data-k="byp" d="M508 100H596"/>
        <path class="fl" data-k="pac" d="M508 100V160M596 160V100"/>
        <path class="fl" data-k="main2" d="M596 100H640V430H26V120H40"/>
        <path class="fl" data-k="balai" d="M90 430V366M70 334V196"/>

        <g class="eq" data-eq="pool" tabindex="0" role="button" aria-label="Bassin">
          <rect x="34" y="64" width="188" height="8" rx="2" class="tile"/>
          <rect x="34" y="64" width="188" height="2" rx="1" fill="rgba(255,255,255,.45)"/>
          <rect x="40" y="72" width="176" height="124" class="wall"/>
          <rect x="50" y="80" width="156" height="106" fill="url(#g-water)"/>
          <rect x="50" y="80" width="156" height="6" fill="rgba(4,44,83,.28)"/>
          <path d="M62 98Q82 93 102 98T142 98T182 98" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="1.5"/>
          <rect x="206" y="86" width="10" height="12" fill="#2E2E2C"/>
          <rect x="216" y="80" width="16" height="24" rx="2" fill="url(#g-pot)" stroke="#7E7C75"/>
          <rect x="118" y="184" width="20" height="4" fill="#2E2E2C"/>
          <rect x="40" y="116" width="12" height="8" fill="#5F5E5A"/>
          <rect x="64" y="184" width="12" height="4" fill="#2E2E2C"/>
          <text x="128" y="128" text-anchor="middle" class="water-lab">Bassin</text>
          <text x="128" y="146" text-anchor="middle" class="water-cap" id="t-water">—</text>
        </g>
        <text class="cap" x="224" y="56" text-anchor="middle">Skimmer</text>
        <text class="cap" x="176" y="276" text-anchor="middle">Bonde de fond</text>
        <g><circle cx="224" cy="160" r="7" fill="url(#g-valve)"/><rect x="222" y="150" width="4" height="20" rx="2" fill="#E24B4A"/></g>
        <g><circle cx="176" cy="250" r="7" fill="url(#g-valve)"/><rect x="166" y="248" width="20" height="4" rx="2" fill="#E24B4A"/></g>

        <g class="eq" data-eq="pump" tabindex="0" role="button" aria-label="Pompe de filtration">
          <rect x="256" y="226" width="32" height="44" rx="4" fill="url(#g-pot)" stroke="#7E7C75"/>
          <rect x="252" y="218" width="40" height="8" rx="2" fill="#B5D4F4" stroke="#378ADD"/>
          <rect x="254" y="219" width="36" height="2" rx="1" fill="rgba(255,255,255,.75)"/>
          <rect x="288" y="232" width="62" height="36" rx="6" fill="url(#g-motor)"/>
          <path d="M304 238V262M316 238V262M328 238V262" stroke="rgba(0,0,0,.35)" stroke-width="1.5"/>
          <path d="M305.5 238V262M317.5 238V262M329.5 238V262" stroke="rgba(255,255,255,.25)" stroke-width="1"/>
          <rect x="350" y="236" width="12" height="28" rx="3" fill="url(#g-motor)"/>
          <rect x="250" y="270" width="116" height="6" rx="2" fill="#4E4D49"/>
          <circle id="led-pump" cx="342" cy="240" r="3" fill="#B4B2A9"/>
          <text class="lab" x="308" y="296" text-anchor="middle">Pompe</text>
          <text class="cap" id="w-pump" x="308" y="312" text-anchor="middle"></text>
        </g>

        <g class="eq" data-eq="filter" tabindex="0" role="button" aria-label="Filtre à sable et vanne 6 voies">
          <rect x="396" y="120" width="72" height="180" rx="30" fill="url(#g-tank)" stroke="#7A786F"/>
          <rect x="396" y="196" width="72" height="5" fill="rgba(0,0,0,.18)"/>
          <path d="M410 134Q432 120 454 134" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="2"/>
          <rect x="426" y="116" width="12" height="6" fill="#7A786F"/>
          <rect x="404" y="300" width="56" height="8" rx="2" fill="#4E4D49"/>
          <circle cx="432" cy="100" r="18" fill="url(#g-knob)"/>
          <circle cx="432" cy="100" r="11" fill="#55544F"/>
          <rect x="432" y="97" width="22" height="6" rx="3" fill="#E24B4A" transform="rotate(-90 432 100)"/>
          <text class="lab" x="432" y="328" text-anchor="middle">Filtre à sable</text>
          <text class="cap" x="432" y="344" text-anchor="middle">Vanne : filtration</text>
        </g>
        <rect x="492" y="34" width="14" height="12" rx="1" fill="#2E2E2C"/>
        <text class="cap" x="514" y="44">Égout</text>
        <text class="cap" x="552" y="84" text-anchor="middle">By-pass</text>
        <g><circle cx="552" cy="100" r="7" fill="url(#g-valve)"/><rect id="vh-byp" x="542" y="98" width="20" height="4" rx="2" fill="#E24B4A"/></g>
        <g><circle cx="508" cy="128" r="7" fill="url(#g-valve)"/><rect id="vh-pin" x="506" y="118" width="4" height="20" rx="2" fill="#E24B4A" transform="rotate(90 508 128)"/></g>
        <g><circle cx="596" cy="128" r="7" fill="url(#g-valve)"/><rect id="vh-pout" x="594" y="118" width="4" height="20" rx="2" fill="#E24B4A" transform="rotate(90 596 128)"/></g>

        <g class="eq" id="pac-g" data-eq="pac" tabindex="0" role="button" aria-label="Pompe à chaleur">
          <rect x="490" y="160" width="124" height="76" rx="5" fill="url(#g-pac)" stroke="#8E8C85"/>
          <rect x="492" y="161" width="120" height="3" rx="1.5" fill="rgba(255,255,255,.85)"/>
          <circle cx="530" cy="198" r="28" fill="url(#g-grille)" stroke="#7E7C75"/>
          <circle cx="530" cy="198" r="20" fill="none" stroke="rgba(255,255,255,.16)"/>
          <g class="fan" id="fan"><path d="M530 198V177M530 198L548 209M530 198L512 209" stroke="#D8D6CE" stroke-width="6" stroke-linecap="round"/></g>
          <circle cx="530" cy="198" r="4" fill="#2B2B29"/>
          <rect x="572" y="176" width="30" height="14" rx="2" fill="#2B2B29"/>
          <text id="pac-disp" x="587" y="187" text-anchor="middle" class="disp">OFF</text>
          <path d="M574 204H602M574 212H602M574 220H602" stroke="#B4B2A9" stroke-width="2"/>
          <text class="lab" x="552" y="256" text-anchor="middle">Pompe à chaleur</text>
          <text class="cap" id="t-pac" x="552" y="272" text-anchor="middle"></text>
        </g>

        <g class="eq" id="g-ph" data-eq="ph" tabindex="0" role="button" aria-label="Traitement secondaire">
          <rect x="414" y="366" width="24" height="34" rx="3" fill="url(#g-can)" stroke="#8E8C85"/>
          <rect x="420" y="360" width="8" height="6" fill="#378ADD"/>
          <path d="M438 380H448" stroke="#888780" stroke-width="1.5"/>
          <rect x="448" y="352" width="44" height="40" rx="4" fill="url(#g-blue)" stroke="#185FA5"/>
          <rect id="scr-ph" x="456" y="360" width="28" height="10" rx="1" fill="#2B2B29"/>
          <path d="M470 392V425" stroke="#888780" stroke-width="1.5"/>
          <circle cx="470" cy="425" r="3" fill="#4E4D49"/>
        </g>
        <g class="eq" id="g-cl" data-eq="cl" tabindex="0" role="button" aria-label="Traitement principal">
          <rect x="536" y="352" width="44" height="40" rx="4" fill="url(#g-yellow)" stroke="#BA7517"/>
          <rect id="scr-cl" x="544" y="360" width="28" height="10" rx="1" fill="#2B2B29"/>
          <path d="M590 380H580" stroke="#888780" stroke-width="1.5"/>
          <rect x="590" y="366" width="24" height="34" rx="3" fill="url(#g-can)" stroke="#8E8C85"/>
          <rect x="596" y="360" width="8" height="6" fill="#E24B4A"/>
          <path d="M558 392V425" stroke="#888780" stroke-width="1.5"/>
          <circle cx="558" cy="425" r="3" fill="#4E4D49"/>
        </g>
        <text class="cap" id="t-ph" x="470" y="456" text-anchor="middle"></text>
        <text class="cap" id="t-cl" x="558" y="456" text-anchor="middle"></text>
        <text class="cap" x="300" y="456" text-anchor="middle">Retour bassin</text>

        <g class="eq" data-eq="bo" tabindex="0" role="button" aria-label="Surpresseur">
          <rect x="52" y="334" width="58" height="32" rx="5" fill="url(#g-motor)"/>
          <rect x="46" y="338" width="6" height="24" rx="2" fill="#4E4D49"/>
          <circle id="led-bo" cx="102" cy="342" r="3" fill="#B4B2A9"/>
          <text class="cap" x="118" y="346">Surpresseur</text>
          <text class="cap" id="w-bo" x="118" y="362"></text>
        </g>

        <g class="alert" id="alert-pump"><path d="M330 200L342 222H318Z"/><text x="330" y="219" text-anchor="middle">!</text></g>
        <g class="alert" id="alert-bo"><path d="M130 306L142 328H118Z"/><text x="130" y="325" text-anchor="middle">!</text></g>
        <g class="alert" id="alert-cl"><path d="M558 318L570 340H546Z"/><text x="558" y="337" text-anchor="middle">!</text></g>
        <g class="alert" id="alert-ph"><path d="M398 360L410 382H386Z"/><text x="398" y="379" text-anchor="middle">!</text></g>
        <g class="alert" id="alert-pac"><path d="M478 138L490 160H466Z"/><text x="478" y="157" text-anchor="middle">!</text></g>
      </svg>
    `;
  }

  _backwashMarkup() {
    return `
      <div class="bw-head">
        <div class="bw-title">
          <h2 class="bw-h">Lavage du filtre à sable</h2>
          <span class="chip warn" id="bw-chip">Action requise</span>
        </div>
        <button class="btn warn" id="bw-stop">Annuler le lavage</button>
      </div>
      <div class="bw-grid">
        <div class="bw-visual">
          <svg viewBox="0 0 300 440" role="img">
            <title>Vanne 6 voies et coupe du filtre</title>
            <defs>
              <marker id="arrow-bw" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>
              <radialGradient id="g2-knob" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#8D8C87"/><stop offset="1" stop-color="#2B2B29"/></radialGradient>
              <linearGradient id="g2-tank" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8E8C85"/><stop offset=".35" stop-color="#E9E7E0"/><stop offset=".7" stop-color="#C4C2BA"/><stop offset="1" stop-color="#83817A"/></linearGradient>
              <linearGradient id="g2-sand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#C38936"/><stop offset=".4" stop-color="#F7CB7E"/><stop offset="1" stop-color="#BA7F31"/></linearGradient>
            </defs>
            <circle cx="150" cy="125" r="66" fill="url(#g2-knob)"/>
            <circle cx="150" cy="125" r="44" fill="#55544F"/>
            <line id="tick-0" x1="150" y1="59" x2="150" y2="49" class="tick"/>
            <line id="tick-1" x1="207" y1="92" x2="216" y2="87" class="tick"/>
            <line id="tick-2" x1="207" y1="158" x2="216" y2="163" class="tick"/>
            <line id="tick-3" x1="150" y1="191" x2="150" y2="201" class="tick"/>
            <line id="tick-4" x1="93" y1="158" x2="84" y2="163" class="tick"/>
            <line id="tick-5" x1="93" y1="92" x2="84" y2="87" class="tick"/>
            <rect id="dh" x="150" y="118" width="58" height="14" rx="7" fill="#E24B4A"/>
            <rect id="dh-hl" x="152" y="119" width="54" height="3" rx="1.5" fill="rgba(255,255,255,.35)"/>
            <circle cx="150" cy="125" r="12" fill="#8A8984"/>
            <circle cx="146" cy="121" r="4" fill="rgba(255,255,255,.3)"/>
            <text class="dl" data-p="filtration" x="150" y="31" text-anchor="middle">Filtration</text>
            <text class="dl" data-p="lavage" x="226" y="84" text-anchor="start">Lavage</text>
            <text class="dl" data-p="rinçage" x="226" y="176" text-anchor="start">Rinçage</text>
            <text class="dl" data-p="égout" x="150" y="226" text-anchor="middle">Égout</text>
            <text class="dl" data-p="circulation" x="74" y="176" text-anchor="end">Circulation</text>
            <text class="dl" data-p="fermé" x="74" y="84" text-anchor="end">Fermé</text>

            <ellipse cx="150" cy="416" rx="44" ry="4" class="shadow"/>
            <path d="M188 290H232" fill="none" stroke="#6B6963" stroke-width="9" stroke-linecap="round"/>
            <path d="M188 290H232" fill="none" stroke="#ADABA3" stroke-width="6" stroke-linecap="round"/>
            <path id="bw-out" class="tk" d="M188 290H232"/>
            <rect x="112" y="262" width="76" height="150" rx="30" fill="url(#g2-tank)" stroke="#7A786F"/>
            <rect x="116" y="316" width="68" height="66" fill="url(#g2-sand)"/>
            <path d="M126 276Q150 262 174 276" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="2"/>
            <path id="bw-up" class="tk" d="M150 372V284" marker-end="url(#arrow-bw)"/>
            <path id="bw-down" class="tk" d="M150 284V372" marker-end="url(#arrow-bw)"/>
            <text class="lab" id="bw-dest" x="240" y="295">—</text>
            <text class="cap" x="150" y="436" text-anchor="middle" id="bw-sand"></text>
          </svg>
        </div>

        <div class="bw-act">
          <div class="instr" id="instr" aria-live="polite"></div>
          <div class="prog" id="prog-w" hidden><i id="prog"></i></div>
          <div class="row"><button class="btn primary" id="bw-main">Étape suivante</button></div>
          <ol class="steps" id="steps">
            <li data-s="1"><span class="n">1</span><div><div class="t">Arrêt de la pompe, vanne sur lavage</div><div class="d">La filtration s'arrête le temps de tourner la manette.</div></div></li>
            <li data-s="2"><span class="n">2</span><div><div class="t">Lavage · <span id="dur-l">2 min</span></div><div class="d">L'eau remonte dans le sable et part à l'égout avec les impuretés.</div></div></li>
            <li data-s="3"><span class="n">3</span><div><div class="t">Arrêt de la pompe, vanne sur rinçage</div><div class="d">Nouvel arrêt pour changer de position.</div></div></li>
            <li data-s="4"><span class="n">4</span><div><div class="t">Rinçage · <span id="dur-r">2 min</span></div><div class="d">L'eau descend dans le sable vers l'égout pour le tasser.</div></div></li>
            <li data-s="5"><span class="n">5</span><div><div class="t">Arrêt de la pompe, vanne sur filtration</div><div class="d">Retour à la position normale, puis retour au synoptique.</div></div></li>
          </ol>
          <dl class="settings">
            <dt>Durée du lavage</dt><dd id="set-l">2 min</dd>
            <dt>Durée du rinçage</dt><dd id="set-r">2 min</dd>
            <dt>Réglage</dt><dd>Configurer · Options avancées</dd>
          </dl>
        </div>
      </div>
    `;
  }

  _css() {
    return `
      :host {
        display: block;
        min-height: 100vh;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
        font-family: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, Roboto, "Segoe UI", system-ui, sans-serif));
        --pc-card: var(--card-background-color, var(--ha-card-background, #fff));
        --pc-ink: var(--primary-text-color, #15201e);
        --pc-muted: var(--secondary-text-color, #586664);
        --pc-line: var(--divider-color, rgba(0, 0, 0, .12));
        --pc-accent: var(--primary-color, #2f7fc1);
        --pc-on-accent: var(--text-primary-color, #fff);
        --pc-run: var(--success-color, #43a047);
        --pc-warn: var(--warning-color, #ffa600);
        --pc-soft: var(--secondary-background-color, rgba(0, 0, 0, .04));
        --pc-wall: #B4B2A9;
        --pc-tile: #D3D1C7;
        --pc-shadow: rgba(0, 0, 0, .16);
      }
      :host([dark]) { --pc-wall: #5F5E5A; --pc-tile: #888780; --pc-shadow: rgba(0, 0, 0, .45); }
      * { box-sizing: border-box; }
      [hidden] { display: none !important; }

      .toolbar { display: flex; align-items: center; gap: 12px; height: var(--header-height, 56px); padding: 0 16px; background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, var(--text-primary-color, #fff)); }
      .toolbar h1 { margin: 0; font-size: 20px; font-weight: 400; }
      .menu-btn { display: none; align-items: center; justify-content: center; width: 40px; height: 40px; margin-left: -8px; border: 0; border-radius: 50%; background: transparent; color: inherit; cursor: pointer; }
      :host([narrow]) .menu-btn { display: inline-flex; }

      .wrap { max-width: 1400px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; }
      .status { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; }
      .chips { display: flex; flex-wrap: wrap; gap: 8px; }
      .chip { font: inherit; font-size: 13px; font-weight: 500; line-height: 1; padding: 7px 12px; border-radius: 999px; background: var(--pc-card); color: var(--pc-muted); border: 1px solid var(--pc-line); white-space: nowrap; }
      .chip.run { background: color-mix(in srgb, var(--pc-run) 16%, transparent); color: var(--pc-run); border-color: transparent; }
      .chip.warn { background: color-mix(in srgb, var(--pc-warn) 18%, transparent); color: var(--pc-warn); border-color: transparent; }
      .chip.temp { cursor: pointer; font-variant-numeric: tabular-nums; color: var(--pc-ink); }

      .grid { display: grid; gap: 16px; grid-template-columns: 1fr; }
      @media (min-width: 1000px) { .grid { grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr); } }
      .card { background: var(--pc-card); border: 1px solid var(--pc-line); border-radius: var(--ha-card-border-radius, 12px); padding: 16px; }
      .panel { display: grid; gap: 12px; align-content: start; scroll-margin-top: 12px; }
      .side { display: grid; gap: 16px; align-content: start; }
      .side h2 { margin: 0 0 12px; font-size: 13px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; color: var(--pc-muted); }

      .btn { font: inherit; font-size: 14px; font-weight: 500; line-height: 1.2; color: var(--pc-ink); background: transparent; border: 1px solid var(--pc-line); border-radius: 8px; padding: 8px 12px; cursor: pointer; }
      .btn:hover { border-color: var(--pc-muted); }
      .btn:focus-visible, .chip.temp:focus-visible, .eq:focus-visible, .menu-btn:focus-visible { outline: 2px solid var(--pc-accent); outline-offset: 2px; }
      .btn.on { background: color-mix(in srgb, var(--pc-accent) 14%, transparent); color: var(--pc-accent); border-color: var(--pc-accent); }
      .btn.primary { background: var(--pc-accent); color: var(--pc-on-accent); border-color: var(--pc-accent); }
      .btn.warn { color: var(--pc-warn); }
      .btn.armed { background: var(--pc-warn); color: #fff; border-color: var(--pc-warn); }
      .btn:disabled { opacity: .45; cursor: not-allowed; }
      .row { display: flex; flex-wrap: wrap; gap: 8px; }
      .gap-top { margin-top: 8px; }
      .line { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; color: var(--pc-muted); }
      .line.warn > span:first-child { color: var(--pc-warn); }
      .muted { color: var(--pc-muted); font-size: 14px; margin-top: 8px; }

      .track { position: relative; height: 22px; background: var(--pc-soft); border: 1px solid var(--pc-line); border-radius: 6px; }
      .seg { position: absolute; top: 0; bottom: 0; background: color-mix(in srgb, var(--pc-accent) 22%, transparent); border-left: 2px solid var(--pc-accent); border-right: 2px solid var(--pc-accent); }
      .now { position: absolute; top: -5px; bottom: -5px; width: 2px; margin-left: -1px; background: var(--pc-ink); }
      .ticks { display: flex; justify-content: space-between; margin-top: 4px; font-size: 12px; color: var(--pc-muted); font-variant-numeric: tabular-nums; }

      .scene { display: block; width: 100%; height: auto; }
      .shadow { fill: var(--pc-shadow); }
      .wall { fill: var(--pc-wall); }
      .tile { fill: var(--pc-tile); }
      .pb { fill: none; stroke: #6B6963; stroke-width: 11; stroke-linecap: round; stroke-linejoin: round; }
      .pm { fill: none; stroke: #ADABA3; stroke-width: 8; stroke-linecap: round; stroke-linejoin: round; }
      .pi { fill: none; stroke: #EFEDE6; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; opacity: .9; }
      .fl { fill: none; stroke: #378ADD; stroke-width: 4; stroke-dasharray: 10 8; stroke-linecap: round; stroke-linejoin: round; opacity: 0; transition: opacity .4s; }
      .fl.on { opacity: 1; }
      .tk { fill: none; stroke: #378ADD; stroke-width: 3; stroke-dasharray: 8 6; opacity: 0; transition: opacity .4s; }
      .tk.on { opacity: 1; }
      .fan { transform-origin: 530px 198px; }
      @media (prefers-reduced-motion: no-preference) {
        .fl, .tk { animation: pc-flow .9s linear infinite; }
        .fan.spin { animation: pc-rot 1s linear infinite; }
      }
      @keyframes pc-flow { to { stroke-dashoffset: -18; } }
      @keyframes pc-rot { to { transform: rotate(360deg); } }
      .eq { cursor: pointer; transition: opacity .3s; }
      .eq:hover { opacity: .85; }
      #pac-g.nocfg { opacity: .42; cursor: default; }
      .lab { font-size: 15px; font-weight: 500; fill: var(--pc-ink); }
      .cap { font-size: 12.5px; fill: var(--pc-muted); }
      .water-lab { font-size: 15px; font-weight: 500; fill: #042C53; }
      .water-cap { font-size: 12.5px; fill: #0C447C; }
      .disp { font-size: 11px; fill: #9FE1CB; font-family: ui-monospace, Consolas, monospace; }
      .alert { opacity: 0; transition: opacity .3s; pointer-events: none; }
      .alert path { fill: #EF9F27; }
      .alert text { font-size: 12px; font-weight: 700; fill: #412402; }

      .bw-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--pc-line); }
      .bw-title { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
      .bw-h { margin: 0; font-size: 20px; font-weight: 500; }
      .bw-grid { display: grid; gap: 18px; grid-template-columns: 1fr; padding-top: 14px; }
      @media (min-width: 700px) { .bw-grid { grid-template-columns: 260px minmax(0, 1fr); } }
      .bw-visual svg { display: block; width: 100%; max-width: 280px; height: auto; margin: 0 auto; }
      .tick { stroke: var(--pc-line); stroke-width: 4; stroke-linecap: round; }
      .dl { font-size: 15px; font-weight: 500; fill: var(--pc-muted); }
      .dl.cur { fill: var(--pc-accent); }
      .dl.tgt { fill: var(--pc-warn); }
      .bw-act { display: grid; gap: 12px; align-content: start; }
      .instr { display: grid; gap: 4px; padding: 12px 14px; border-radius: 8px; background: color-mix(in srgb, var(--pc-warn) 16%, transparent); color: var(--pc-muted); }
      .instr strong { font-size: 18px; font-weight: 500; color: var(--pc-ink); }
      .prog { height: 6px; background: var(--pc-soft); border: 1px solid var(--pc-line); border-radius: 3px; overflow: hidden; }
      .prog i { display: block; height: 100%; width: 0; background: var(--pc-warn); transition: width .5s linear; }
      .steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
      .steps li { display: grid; grid-template-columns: 26px 1fr; gap: 10px; align-items: start; padding: 7px 10px; border: 1px solid var(--pc-line); border-radius: 8px; }
      .steps .n { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; font-size: 13px; font-weight: 500; background: var(--pc-soft); color: var(--pc-muted); border: 1px solid var(--pc-line); }
      .steps .t { font-weight: 500; line-height: 1.3; }
      .steps .d { font-size: 14px; line-height: 1.35; color: var(--pc-muted); }
      .steps li.cur { border-color: var(--pc-warn); background: color-mix(in srgb, var(--pc-warn) 14%, transparent); }
      .steps li.cur .n { background: var(--pc-warn); color: #fff; border-color: transparent; }
      .steps li.done .n { background: var(--pc-run); color: #fff; border-color: transparent; }
      .steps li.done .t { color: var(--pc-muted); }
      .settings { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; margin: 0; font-size: 14px; }
      .settings dt { color: var(--pc-muted); }
      .settings dd { margin: 0; font-variant-numeric: tabular-nums; }
    `;
  }
}

customElements.define('pool-control-panel', PoolControlPanel);
