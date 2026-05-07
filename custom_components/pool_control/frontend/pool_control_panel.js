/**
 * Pool Control — Panel custom pour Home Assistant
 *
 * Web Component vanilla JS — pas de build, pas de dépendances.
 * Lit les entités via hass.states, écrit via hass.callService().
 */

class PoolControlPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._rendered = false;
    this._waterTempEntity = null;
    this._airTempEntity = null;
    this._instancePrefix = 'pool_control';
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      const cfg = (this.panel && this.panel.config) || {};
      if (cfg.water_entity) this._waterTempEntity = cfg.water_entity;
      if (cfg.air_entity) this._airTempEntity = cfg.air_entity;
      if (cfg.instance_prefix) this._instancePrefix = cfg.instance_prefix;
      this._render();
      this._rendered = true;
    }
    this._update();
  }

  get hass() { return this._hass; }
  set narrow(v) { this._narrow = v; }
  set route(v) { this._route = v; }
  set panel(v) { this._panel = v; }
  get panel() { return this._panel; }

  _entityState(id) {
    if (!this._hass || !this._hass.states[id]) return null;
    return this._hass.states[id];
  }

  _stateText(id, fallback = '—') {
    const s = this._entityState(id);
    return s ? s.state : fallback;
  }

  _callService(domain, service, target) {
    if (!this._hass) return;
    return this._hass.callService(domain, service, { entity_id: target });
  }

  _pressButton(buttonId) {
    return this._callService('button', 'press', buttonId);
  }

  _isFiltrationRunning() {
    const s = this._stateText(`sensor.${this._instancePrefix}_filtration_status`).toLowerCase();
    return /actif|filtration|lavage|rin|surpress|marche/i.test(s) && !/arr[êe]t|stop|inactif/i.test(s);
  }

  _controlMode() {
    const raw = this._stateText(`sensor.${this._instancePrefix}_control_status`);
    const lower = raw.toLowerCase();
    let mode = 'inconnu';
    if (lower.includes('actif')) mode = 'actif';
    else if (lower.includes('auto')) mode = 'auto';
    else if (lower.includes('inactif')) mode = 'inactif';
    let season = 'saison';
    if (lower.includes('hivernage') || lower.includes('hiver')) season = 'hivernage';
    return { mode, season, raw };
  }

  _backwashStep() {
    const s = this._stateText(`sensor.${this._instancePrefix}_backwash_status`).toLowerCase();
    if (s.includes('position lavage')) return 'pos_lavage';
    if (s.includes('position rin')) return 'pos_rincage';
    if (s.includes('position filtration') || (s.includes('filtration') && s.includes('arr'))) return 'pos_filtration';
    if (s.includes('lavage')) return 'lavage';
    if (s.includes('rin')) return 'rincage';
    if (s.includes('filtration')) return 'filtration_finale';
    return 'idle';
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          background: var(--primary-background-color, #0b1620);
          color: var(--primary-text-color, #e8eef3);
          min-height: 100vh;
          font-family: var(--paper-font-body1_-_font-family, 'Roboto', 'Segoe UI', sans-serif);
        }
        .app-header {
          position: sticky; top: 0; z-index: 10;
          background: var(--app-header-background-color, #1a3a52);
          color: var(--app-header-text-color, #fff);
          padding: 0 16px; height: 56px;
          display: flex; align-items: center; gap: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .app-header .menu-btn {
          background: none; border: none; color: inherit;
          cursor: pointer; padding: 8px; font-size: 24px; line-height: 1;
        }
        .app-header h1 { margin: 0; font-size: 20px; font-weight: 400; letter-spacing: 0.02em; }
        .app-header .status-badge {
          margin-left: auto; padding: 4px 12px; border-radius: 12px;
          font-size: 12px; font-weight: 500; letter-spacing: 0.05em;
          text-transform: uppercase; background: rgba(255,255,255,0.15);
        }
        .app-header .status-badge.running { background: #10b981; }
        .app-header .status-badge.winter  { background: #3b82f6; }
        .app-header .status-badge.off     { background: #6b7280; }

        .container {
          max-width: 1400px; margin: 0 auto; padding: 20px;
          display: grid; grid-template-columns: 1fr; gap: 20px;
        }
        @media (min-width: 1100px) {
          .container { grid-template-columns: 1fr 1.5fr; }
          .col-schema { grid-column: 1 / -1; }
        }
        .card {
          background: var(--card-background-color, #0f2030);
          border: 1px solid var(--divider-color, rgba(255,255,255,0.08));
          border-radius: 12px; padding: 20px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }
        .card-title {
          font-size: 13px; font-weight: 500; text-transform: uppercase;
          letter-spacing: 0.15em; color: #f4a261; margin: 0 0 16px;
          display: flex; align-items: center; gap: 8px;
        }
        .card-title .ico { font-size: 18px; }

        .info-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: var(--secondary-text-color, #8a9ba8); font-size: 13px; }
        .info-value { font-weight: 500; font-size: 14px; text-align: right; }
        .info-value.big { font-size: 18px; color: #4cc9f0; }

        .temp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
        .temp-tile {
          background: linear-gradient(135deg, rgba(76,201,240,0.08), rgba(39,125,161,0.15));
          border: 1px solid rgba(76,201,240,0.2);
          border-radius: 10px; padding: 16px; text-align: center;
        }
        .temp-tile.air {
          background: linear-gradient(135deg, rgba(244,162,97,0.08), rgba(231,111,81,0.15));
          border-color: rgba(244,162,97,0.2);
        }
        .temp-tile-label {
          font-size: 11px; text-transform: uppercase; letter-spacing: 0.15em;
          color: #8a9ba8; margin-bottom: 6px;
        }
        .temp-tile-value { font-size: 28px; font-weight: 300; }
        .temp-tile-unit { font-size: 16px; color: #8a9ba8; margin-left: 2px; }

        .btn-row { display: grid; gap: 8px; margin-top: 12px; }
        .btn-row.cols-2 { grid-template-columns: 1fr 1fr; }
        .btn-row.cols-3 { grid-template-columns: 1fr 1fr 1fr; }

        button.btn {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: var(--primary-text-color, #e8eef3);
          padding: 12px 14px; border-radius: 8px;
          font-size: 13px; font-weight: 500; cursor: pointer;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          transition: all 0.2s ease; font-family: inherit;
        }
        button.btn:hover:not(:disabled) {
          background: rgba(255,255,255,0.1);
          border-color: rgba(255,255,255,0.2);
          transform: translateY(-1px);
        }
        button.btn:active:not(:disabled) { transform: translateY(0); }
        button.btn:disabled { opacity: 0.4; cursor: not-allowed; }
        button.btn .ico { font-size: 18px; }
        button.btn.active { background: var(--accent, #f4a261); color: #0b1620; border-color: var(--accent, #f4a261); }
        button.btn.primary { background: #4cc9f0; color: #0b1620; border-color: #4cc9f0; }
        button.btn.primary:hover { background: #6ed1f4; }
        button.btn.success { background: #10b981; color: #fff; border-color: #10b981; }
        button.btn.success:hover { background: #34d399; }
        button.btn.danger  { background: #ef4444; color: #fff; border-color: #ef4444; }
        button.btn.danger:hover { background: #f87171; }
        button.btn.warning { background: #f4a261; color: #0b1620; border-color: #f4a261; }
        button.btn.winter  { background: #3b82f6; color: #fff; border-color: #3b82f6; }

        .vanne-prompt {
          background: linear-gradient(135deg, rgba(244,162,97,0.2), rgba(231,111,81,0.3));
          border: 1px solid rgba(244,162,97,0.5);
          border-radius: 10px; padding: 16px; margin-top: 12px;
          text-align: center; animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%,100% { box-shadow: 0 0 0 0 rgba(244,162,97,0.4); }
          50%     { box-shadow: 0 0 0 8px rgba(244,162,97,0); }
        }
        .vanne-prompt strong { color: #f4a261; }

        .schema-wrap {
          background: linear-gradient(135deg, #0f2030 0%, #0b1620 100%);
          border-radius: 10px; padding: 8px; overflow: hidden;
        }
        svg.pool-svg { width: 100%; height: auto; display: block; }

        .water-particle { fill:#90e0ef; filter:drop-shadow(0 0 3px #4cc9f0); }
        .stopped .water-particle { opacity:0; }
        .running .water-particle { opacity:1; }

        .running .flow-asp .water-particle { animation: flowAsp 4s linear infinite; }
        .running .flow-pf  .water-particle { animation: flowPf  3s linear infinite; }
        .running .flow-fr  .water-particle { animation: flowFr  4s linear infinite; }
        .running .flow-ret .water-particle { animation: flowRet 3s linear infinite; }

        @keyframes flowAsp { from{offset-distance:0%} to{offset-distance:100%} }
        @keyframes flowPf  { from{offset-distance:0%} to{offset-distance:100%} }
        @keyframes flowFr  { from{offset-distance:0%} to{offset-distance:100%} }
        @keyframes flowRet { from{offset-distance:0%} to{offset-distance:100%} }

        .p1{animation-delay:0s !important}
        .p2{animation-delay:-0.5s !important}
        .p3{animation-delay:-1s !important}
        .p4{animation-delay:-1.5s !important}
        .p5{animation-delay:-2s !important}
        .p6{animation-delay:-2.5s !important}
        .p7{animation-delay:-3s !important}
        .p8{animation-delay:-3.5s !important}

        .pump-rotor { transform-origin: 555px 360px; }
        .running .pump-rotor { animation: rot 1.2s linear infinite; }
        @keyframes rot { to { transform: rotate(360deg); } }

        .running .water-surface { animation: wave 4s ease-in-out infinite; }
        @keyframes wave { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-2px)} }

        .status-led { fill:#7a8794; }
        .running .status-led { fill:#10b981; filter:drop-shadow(0 0 6px #10b981); }
        .backwash-active .filtre-rect { stroke: #f4a261; stroke-width: 3; }

        .footer-info {
          text-align: center; color: #6b7280; font-size: 11px;
          letter-spacing: 0.15em; text-transform: uppercase;
          padding: 20px 0 10px;
        }
      </style>

      <div class="app-header">
        <button class="menu-btn" id="menu-btn" title="Menu">☰</button>
        <h1>🏊 Pool Control</h1>
        <span class="status-badge" id="header-badge">—</span>
      </div>

      <div class="container">
        <div class="col-info">

          <section class="card">
            <h2 class="card-title"><span class="ico">📊</span> État général</h2>

            <div class="temp-grid">
              <div class="temp-tile">
                <div class="temp-tile-label">💧 Eau</div>
                <div class="temp-tile-value" id="temp-water">—<span class="temp-tile-unit">°C</span></div>
              </div>
              <div class="temp-tile air">
                <div class="temp-tile-label">🌡️ Air</div>
                <div class="temp-tile-value" id="temp-air">—<span class="temp-tile-unit">°C</span></div>
              </div>
            </div>

            <div class="info-row">
              <span class="info-label">Statut</span>
              <span class="info-value big" id="info-control"></span>
            </div>
            <div class="info-row">
              <span class="info-label">Filtration</span>
              <span class="info-value" id="info-filt-status">—</span>
            </div>
            <div class="info-row">
              <span class="info-label">Temps calculé</span>
              <span class="info-value" id="info-filt-time">—</span>
            </div>
            <div class="info-row">
              <span class="info-label">Planning</span>
              <span class="info-value" id="info-filt-schedule" style="font-size:12px; max-width:60%;">—</span>
            </div>

            <div class="btn-row">
              <button class="btn warning" id="btn-reset">
                <span class="ico">🔄</span> Recalculer le planning
              </button>
            </div>
          </section>

          <section class="card">
            <h2 class="card-title"><span class="ico">🎛️</span> Mode de contrôle</h2>

            <div class="btn-row cols-3">
              <button class="btn" id="btn-active" data-mode="actif">
                <span class="ico">▶️</span> Actif
              </button>
              <button class="btn" id="btn-auto" data-mode="auto">
                <span class="ico">🤖</span> Auto
              </button>
              <button class="btn" id="btn-inactive" data-mode="inactif">
                <span class="ico">⏹️</span> Inactif
              </button>
            </div>

            <div class="btn-row cols-2" style="margin-top: 12px;">
              <button class="btn" id="btn-season" data-season="saison">
                <span class="ico">☀️</span> Saison
              </button>
              <button class="btn" id="btn-winter" data-season="hivernage">
                <span class="ico">❄️</span> Hivernage
              </button>
            </div>
          </section>

          <section class="card">
            <h2 class="card-title"><span class="ico">🌀</span> Surpresseur</h2>

            <div class="info-row">
              <span class="info-label">État</span>
              <span class="info-value" id="info-booster">—</span>
            </div>

            <div class="btn-row cols-2">
              <button class="btn success" id="btn-booster">
                <span class="ico">▶️</span> Démarrer
              </button>
              <button class="btn danger" id="btn-stop-booster">
                <span class="ico">⏹</span> Stop
              </button>
            </div>
          </section>

          <section class="card">
            <h2 class="card-title"><span class="ico">🧴</span> Lavage du filtre</h2>

            <div class="info-row">
              <span class="info-label">Étape</span>
              <span class="info-value" id="info-backwash">—</span>
            </div>

            <div id="vanne-prompt-zone"></div>

            <div class="btn-row cols-2">
              <button class="btn primary" id="btn-backwash">
                <span class="ico">⏭️</span> Étape suivante
              </button>
              <button class="btn danger" id="btn-stop-backwash">
                <span class="ico">⏹</span> Stop
              </button>
            </div>
          </section>

        </div>

        <div class="col-schema">
          <section class="card">
            <h2 class="card-title"><span class="ico">🔧</span> Circuit hydraulique</h2>
            <div class="schema-wrap" id="schema-wrap">
              ${this._svgMarkup()}
            </div>
            <div class="footer-info" id="schema-info">—</div>
          </section>
        </div>

      </div>
    `;

    const $ = (s) => this.shadowRoot.querySelector(s);

    $('#menu-btn').addEventListener('click', () => {
      this.dispatchEvent(new CustomEvent('hass-toggle-menu', { bubbles: true, composed: true }));
    });
    $('#btn-reset').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_reset`));
    $('#btn-active').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_active`));
    $('#btn-auto').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_auto`));
    $('#btn-inactive').addEventListener('click', () => {
      if (confirm('Désactiver complètement le contrôle ?'))
        this._pressButton(`button.${this._instancePrefix}_inactive`);
    });
    $('#btn-season').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_season`));
    $('#btn-winter').addEventListener('click', () => {
      if (confirm('Basculer en mode hivernage ?'))
        this._pressButton(`button.${this._instancePrefix}_winter`);
    });
    $('#btn-booster').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_booster`));
    $('#btn-stop-booster').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_stop`));
    $('#btn-backwash').addEventListener('click', () => this._pressButton(`button.${this._instancePrefix}_backwash`));
    $('#btn-stop-backwash').addEventListener('click', () => {
      if (confirm('Interrompre le lavage en cours ?'))
        this._pressButton(`button.${this._instancePrefix}_stop`);
    });
  }

  _update() {
    if (!this._rendered) return;
    const $ = (s) => this.shadowRoot.querySelector(s);

    const water = this._waterTempEntity ? this._entityState(this._waterTempEntity) : null;
    const air   = this._airTempEntity   ? this._entityState(this._airTempEntity)   : null;
    const fmtTemp = (st) => {
      if (!st) return '—';
      const v = parseFloat(st.state);
      return isNaN(v) ? '—' : v.toFixed(1);
    };
    $('#temp-water').innerHTML = `${fmtTemp(water)}<span class="temp-tile-unit">°C</span>`;
    $('#temp-air').innerHTML   = `${fmtTemp(air)}<span class="temp-tile-unit">°C</span>`;

    const ctrl = this._controlMode();
    $('#info-control').textContent = ctrl.raw;
    $('#info-filt-status').textContent   = this._stateText(`sensor.${this._instancePrefix}_filtration_status`);
    $('#info-filt-time').textContent     = this._stateText(`sensor.${this._instancePrefix}_filtration_time`);
    $('#info-filt-schedule').textContent = this._stateText(`sensor.${this._instancePrefix}_filtration_schedule`);

    const running = this._isFiltrationRunning();
    const badge = $('#header-badge');
    if (ctrl.season === 'hivernage') {
      badge.className = 'status-badge winter';
      badge.textContent = '❄ Hivernage';
    } else if (running) {
      badge.className = 'status-badge running';
      badge.textContent = '● En fonction';
    } else if (ctrl.mode === 'inactif') {
      badge.className = 'status-badge off';
      badge.textContent = '○ Désactivé';
    } else {
      badge.className = 'status-badge';
      badge.textContent = '○ À l\'arrêt';
    }

    $('#btn-active').classList.toggle('active', ctrl.mode === 'actif');
    $('#btn-auto').classList.toggle('active', ctrl.mode === 'auto');
    $('#btn-inactive').classList.toggle('active', ctrl.mode === 'inactif');
    $('#btn-season').classList.toggle('active', ctrl.season === 'saison');
    $('#btn-winter').classList.toggle('active', ctrl.season === 'hivernage');

    $('#info-booster').textContent = this._stateText(`sensor.${this._instancePrefix}_booster_status`);

    const bwState = this._stateText(`sensor.${this._instancePrefix}_backwash_status`);
    $('#info-backwash').textContent = bwState;
    const step = this._backwashStep();

    const promptZone = $('#vanne-prompt-zone');
    let promptHtml = '';
    if (step === 'pos_lavage')
      promptHtml = `<div class="vanne-prompt">👉 Positionnez la vanne sur <strong>LAVAGE</strong>, puis appuyez sur « Étape suivante »</div>`;
    else if (step === 'pos_rincage')
      promptHtml = `<div class="vanne-prompt">👉 Positionnez la vanne sur <strong>RINÇAGE</strong>, puis appuyez sur « Étape suivante »</div>`;
    else if (step === 'pos_filtration')
      promptHtml = `<div class="vanne-prompt">👉 Repositionnez la vanne sur <strong>FILTRATION</strong>, puis appuyez sur « Étape suivante »</div>`;
    promptZone.innerHTML = promptHtml;

    const wrap = $('#schema-wrap');
    const svg = wrap.querySelector('svg');
    if (svg) {
      svg.classList.toggle('running', running);
      svg.classList.toggle('stopped', !running);
      svg.classList.toggle('backwash-active', step === 'lavage' || step === 'rincage');
      const led = svg.querySelector('#status-led-text');
      if (led) led.textContent = running ? 'EN FONCTION' : 'À L\'ARRÊT';
    }

    let info = '';
    if (running) {
      if (step === 'lavage') info = '🧴 Lavage en cours — eau évacuée à l\'égout';
      else if (step === 'rincage') info = '💧 Rinçage du filtre en cours';
      else info = '🔄 Filtration active — circulation normale';
    } else {
      info = '⏸ Filtration à l\'arrêt';
    }
    $('#schema-info').textContent = info;
  }

  _svgMarkup() {
    return `
      <svg class="pool-svg stopped" viewBox="0 0 1100 560" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="wG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#90e0ef" stop-opacity="0.95"/>
            <stop offset="50%" stop-color="#4cc9f0" stop-opacity="0.85"/>
            <stop offset="100%" stop-color="#277da1"/>
          </linearGradient>
          <linearGradient id="tG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#244e6e"/><stop offset="100%" stop-color="#1a3a52"/>
          </linearGradient>
          <linearGradient id="mG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#d8e1ea"/>
            <stop offset="50%" stop-color="#b8c5d1"/>
            <stop offset="100%" stop-color="#7a8794"/>
          </linearGradient>
          <linearGradient id="fG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3a4a5a"/>
            <stop offset="100%" stop-color="#1a2530"/>
          </linearGradient>
          <linearGradient id="sG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#d4a574"/>
            <stop offset="100%" stop-color="#a07a4f"/>
          </linearGradient>
        </defs>

        <circle class="status-led" cx="1060" cy="30" r="6"/>
        <text id="status-led-text" x="1045" y="34" text-anchor="end"
              font-family="Georgia,serif" font-size="11" fill="#8a9ba8"
              letter-spacing="0.1em">À L'ARRÊT</text>

        <rect x="60" y="115" width="280" height="12" fill="#7a8794" rx="2"/>
        <path d="M 70,127 L 70,360 Q 70,375 85,375 L 325,375 Q 340,375 340,360 L 340,127 Z" fill="url(#tG)"/>
        <path d="M 80,140 L 80,360 Q 80,365 85,365 L 325,365 Q 330,365 330,360 L 330,140 Z" fill="url(#wG)"/>
        <g class="water-surface">
          <path d="M 80,148 Q 115,143 145,148 T 205,148 T 265,148 T 330,148"
                stroke="#caf0f8" stroke-width="1" fill="none" opacity="0.8"/>
        </g>

        <rect x="155" y="140" width="50" height="50" fill="#0f2030" stroke="#7a8794" stroke-width="1.5"/>
        <rect x="158" y="143" width="44" height="3" fill="#9aa8b5"/>
        <circle cx="180" cy="105" r="14" fill="#f4a261"/>
        <text x="180" y="110" text-anchor="middle" font-family="Georgia" font-size="14"
              font-weight="bold" fill="#0b1620">1</text>

        <rect x="305" y="195" width="25" height="14" fill="#0f2030" stroke="#7a8794"/>
        <circle cx="365" cy="202" r="14" fill="#f4a261"/>
        <text x="365" y="207" text-anchor="middle" font-family="Georgia" font-size="14"
              font-weight="bold" fill="#0b1620">4</text>

        <g fill="#2c3e50" stroke="#1a2530">
          <rect x="174" y="178" width="12" height="265"/>
          <rect x="174" y="434" width="345" height="12"/>
          <rect x="504" y="356" width="12" height="90"/>
          <rect x="595" y="354" width="130" height="12"/>
          <rect x="713" y="305" width="14" height="61"/>
          <rect x="795" y="224" width="90" height="12"/>
          <rect x="874" y="230" width="12" height="216"/>
          <rect x="874" y="434" width="146" height="12"/>
          <rect x="1004" y="195" width="12" height="251"/>
          <rect x="958" y="195" width="58" height="12"/>
        </g>

        <ellipse cx="555" cy="360" rx="45" ry="35" fill="url(#mG)" stroke="#1a2530" stroke-width="1.5"/>
        <ellipse cx="555" cy="360" rx="32" ry="25" fill="#2c3e50"/>
        <g class="pump-rotor">
          <circle cx="555" cy="360" r="22" fill="#1a2530"/>
          <path d="M 555,340 Q 565,360 555,380 Q 545,360 555,340" fill="#7a8794"/>
          <path d="M 535,360 Q 555,350 575,360 Q 555,370 535,360" fill="#7a8794"/>
          <circle cx="555" cy="360" r="4" fill="#f4a261"/>
        </g>
        <rect x="600" y="340" width="40" height="40" rx="3" fill="url(#mG)" stroke="#1a2530"/>
        <circle cx="555" cy="290" r="14" fill="#f4a261"/>
        <text x="555" y="295" text-anchor="middle" font-family="Georgia" font-size="14"
              font-weight="bold" fill="#0b1620">2</text>

        <rect x="730" y="200" width="50" height="30" rx="3" fill="url(#mG)" stroke="#1a2530"/>
        <circle cx="755" cy="215" r="8" fill="#1a2530"/>
        <ellipse cx="755" cy="240" rx="45" ry="10" fill="url(#fG)" stroke="#1a2530"/>
        <rect class="filtre-rect" x="710" y="240" width="90" height="160" fill="url(#fG)" stroke="#1a2530"/>
        <ellipse cx="755" cy="400" rx="45" ry="10" fill="#1a2530"/>
        <rect x="725" y="320" width="60" height="75" fill="url(#sG)"/>
        <rect x="710" y="250" width="90" height="70" fill="#4cc9f0" opacity="0.3"/>
        <circle cx="755" cy="105" r="14" fill="#f4a261"/>
        <text x="755" y="110" text-anchor="middle" font-family="Georgia" font-size="14"
              font-weight="bold" fill="#0b1620">3</text>

        <g class="flow-asp">
          ${[1,2,3,4,5,6,7,8].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 180,180 L 180,440 L 510,440 L 510,360')"/>`
          ).join('')}
        </g>
        <g class="flow-pf">
          ${[1,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 600,360 L 720,360 L 720,310')"/>`
          ).join('')}
        </g>
        <g class="flow-fr">
          ${[1,2,3,4,5,6,7,8].map(i =>
            `<circle class="water-particle p${i}" r="2.5"
             style="offset-path: path('M 800,230 L 880,230 L 880,440 L 950,440')"/>`
          ).join('')}
        </g>
        <g class="flow-ret">
          ${[1,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 950,440 L 1010,440 L 1010,200 L 960,200')"/>`
          ).join('')}
        </g>

        <text x="200" y="80" text-anchor="middle" font-family="Georgia,serif"
              font-size="11" fill="#f4a261" letter-spacing="0.15em">BASSIN</text>
        <text x="755" y="540" text-anchor="middle" font-family="Georgia,serif"
              font-size="10" fill="#8a9ba8" letter-spacing="0.15em">LOCAL TECHNIQUE</text>

        <text x="200" y="500" text-anchor="middle" font-family="Georgia,serif"
              font-size="9" fill="#6b7280">1·skimmer  2·pompe  3·filtre  4·refoulement</text>
      </svg>
    `;
  }
}

customElements.define('pool-control-panel', PoolControlPanel);
