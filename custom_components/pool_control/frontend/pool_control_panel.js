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
          min-height: 100vh;
          color: var(--primary-text-color, #e8eef3);
          font-family: var(--paper-font-body1_-_font-family, 'Inter', 'Roboto', 'Segoe UI', system-ui, sans-serif);
          background:
            radial-gradient(circle at 20% 0%, rgba(76, 201, 240, 0.10), transparent 55%),
            radial-gradient(circle at 80% 100%, rgba(244, 162, 97, 0.08), transparent 55%),
            linear-gradient(180deg, var(--primary-background-color, #0a1420) 0%, var(--primary-background-color, #060d18) 100%);

          /* Design tokens */
          --gap-xs: 8px;
          --gap-sm: 12px;
          --gap-md: 16px;
          --gap-lg: 24px;
          --gap-xl: 32px;

          --radius-sm: 10px;
          --radius-md: 14px;
          --radius-lg: 20px;

          --ease: cubic-bezier(0.4, 0, 0.2, 1);
          --t-fast: 160ms;
          --t-base: 220ms;
          --t-slow: 320ms;

          --accent: #f4a261;
          --accent-water: #4cc9f0;
          --accent-air: #f4a261;
          --c-success: #10b981;
          --c-danger: #ef4444;
          --c-winter: #3b82f6;

          --glass-bg: rgba(15, 32, 48, 0.55);
          --glass-border: rgba(255, 255, 255, 0.08);
          --glass-border-top: rgba(255, 255, 255, 0.14);
          --glass-shadow:
            0 8px 32px -8px rgba(0, 0, 0, 0.45),
            inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }

        /* ─────────────── HEADER ─────────────── */
        .app-header {
          position: sticky;
          top: 0;
          z-index: 10;
          height: 64px;
          padding: 0 var(--gap-lg);
          display: flex;
          align-items: center;
          gap: var(--gap-md);
          background: rgba(8, 16, 26, 0.72);
          backdrop-filter: blur(20px) saturate(180%);
          -webkit-backdrop-filter: blur(20px) saturate(180%);
          border-bottom: 1px solid var(--glass-border);
        }
        .menu-btn {
          width: 40px; height: 40px;
          display: inline-flex; align-items: center; justify-content: center;
          background: transparent;
          border: none;
          color: inherit;
          cursor: pointer;
          font-size: 22px;
          border-radius: 10px;
          transition: background var(--t-fast) var(--ease);
        }
        .menu-btn:hover { background: rgba(255, 255, 255, 0.06); }

        .header-titles {
          display: flex; flex-direction: column; gap: 2px; line-height: 1.1;
        }
        .header-title {
          margin: 0;
          font-size: 17px;
          font-weight: 600;
          letter-spacing: -0.01em;
        }
        .header-subtitle {
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--secondary-text-color, #8a9ba8);
        }

        .status-badge {
          margin-left: auto;
          padding: 6px 14px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.10em;
          text-transform: uppercase;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.10);
          transition: all var(--t-base) var(--ease);
        }
        .status-badge.running {
          background: rgba(16, 185, 129, 0.18);
          color: #6ee7b7;
          border-color: rgba(16, 185, 129, 0.4);
          box-shadow: 0 0 24px -6px rgba(16, 185, 129, 0.5);
        }
        .status-badge.winter {
          background: rgba(59, 130, 246, 0.18);
          color: #93c5fd;
          border-color: rgba(59, 130, 246, 0.4);
          box-shadow: 0 0 24px -6px rgba(59, 130, 246, 0.5);
        }
        .status-badge.off {
          background: rgba(107, 114, 128, 0.18);
          color: #d1d5db;
          border-color: rgba(107, 114, 128, 0.3);
        }

        /* ─────────────── LAYOUT ─────────────── */
        .container {
          max-width: 1440px;
          margin: 0 auto;
          padding: var(--gap-lg) var(--gap-md);
          display: grid;
          grid-template-columns: repeat(12, 1fr);
          gap: var(--gap-md);
        }
        @media (min-width: 720px) {
          .container { padding: var(--gap-xl); gap: var(--gap-lg); }
        }

        /* Mobile: tout en pleine largeur */
        .area-hero,
        .area-modes,
        .area-schema,
        .area-stack { grid-column: span 12; }
        .area-stack { display: grid; gap: var(--gap-md); }

        /* Desktop: grille 12 cols */
        @media (min-width: 1100px) {
          .area-hero    { grid-column: span 8; }
          .area-modes   { grid-column: span 4; }
          .area-schema  { grid-column: span 8; }
          .area-stack   { grid-column: span 4; }
        }

        /* ─────────────── CARDS (glassmorphism) ─────────────── */
        .card {
          position: relative;
          background: var(--glass-bg);
          backdrop-filter: blur(24px) saturate(180%);
          -webkit-backdrop-filter: blur(24px) saturate(180%);
          border: 1px solid var(--glass-border);
          border-top-color: var(--glass-border-top);
          border-radius: var(--radius-lg);
          padding: var(--gap-lg);
          box-shadow: var(--glass-shadow);
          opacity: 0;
          transform: translateY(12px);
          animation: card-in var(--t-slow) var(--ease) forwards;
        }
        .card:nth-child(1) { animation-delay: 0ms; }
        .card:nth-child(2) { animation-delay: 50ms; }
        .card:nth-child(3) { animation-delay: 100ms; }
        .card:nth-child(4) { animation-delay: 150ms; }
        .area-stack .card:nth-child(2) { animation-delay: 200ms; }

        @keyframes card-in {
          to { opacity: 1; transform: translateY(0); }
        }

        .card-head {
          display: flex; align-items: center; justify-content: space-between;
          gap: var(--gap-sm);
          margin-bottom: var(--gap-md);
        }
        .card-title {
          margin: 0;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--accent);
          display: flex; align-items: center; gap: 8px;
        }
        .card-title .ico { font-size: 16px; }

        .card-aside {
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--secondary-text-color, #8a9ba8);
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid var(--glass-border);
        }

        /* ─────────────── HERO (températures + statut) ─────────────── */
        .hero-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--gap-md);
          margin-bottom: var(--gap-md);
        }
        .stat {
          position: relative;
          padding: var(--gap-md);
          border-radius: var(--radius-md);
          background: linear-gradient(135deg, rgba(76,201,240,0.06), rgba(76,201,240,0.02));
          border: 1px solid rgba(76, 201, 240, 0.18);
          overflow: hidden;
        }
        .stat::after {
          content: '';
          position: absolute; inset: 0;
          background: radial-gradient(circle at 100% 0%, rgba(76,201,240,0.18), transparent 60%);
          pointer-events: none;
        }
        .stat.air {
          background: linear-gradient(135deg, rgba(244,162,97,0.06), rgba(244,162,97,0.02));
          border-color: rgba(244, 162, 97, 0.18);
        }
        .stat.air::after {
          background: radial-gradient(circle at 100% 0%, rgba(244,162,97,0.18), transparent 60%);
        }
        .stat-label {
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--secondary-text-color, #8a9ba8);
          display: flex; align-items: center; gap: 6px;
          position: relative;
        }
        .stat-value {
          margin-top: 6px;
          font-size: 44px;
          font-weight: 200;
          line-height: 1.0;
          letter-spacing: -0.03em;
          font-feature-settings: "tnum";
          position: relative;
        }
        .temp-tile-unit {
          font-size: 18px;
          font-weight: 300;
          color: var(--secondary-text-color, #8a9ba8);
          margin-left: 4px;
        }

        .info-list {
          display: flex; flex-direction: column;
          background: rgba(0, 0, 0, 0.18);
          border-radius: var(--radius-md);
          border: 1px solid var(--glass-border);
          padding: 4px var(--gap-md);
        }
        .info-row {
          display: flex; align-items: center; justify-content: space-between;
          padding: var(--gap-sm) 0;
          gap: var(--gap-md);
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .info-row:last-child { border-bottom: none; }
        .info-label {
          font-size: 12px;
          font-weight: 500;
          letter-spacing: 0.05em;
          color: var(--secondary-text-color, #8a9ba8);
          flex-shrink: 0;
        }
        .info-value {
          font-size: 14px;
          font-weight: 500;
          text-align: right;
          font-feature-settings: "tnum";
        }
        .info-value.lead {
          font-size: 22px;
          font-weight: 300;
          color: var(--accent-water);
          letter-spacing: -0.01em;
        }
        .info-value.schedule {
          font-size: 12px;
          color: var(--secondary-text-color, #8a9ba8);
          max-width: 60%;
        }

        /* ─────────────── BUTTONS ─────────────── */
        .actions { display: grid; gap: var(--gap-sm); margin-top: var(--gap-md); }
        .actions.cols-2 { grid-template-columns: 1fr 1fr; }

        button.btn {
          appearance: none;
          font-family: inherit;
          font-size: 13px;
          font-weight: 500;
          letter-spacing: 0.02em;
          color: var(--primary-text-color, #e8eef3);
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 12px 16px;
          cursor: pointer;
          display: inline-flex; align-items: center; justify-content: center; gap: 8px;
          transition: transform var(--t-fast) var(--ease),
                      background var(--t-fast) var(--ease),
                      border-color var(--t-fast) var(--ease),
                      box-shadow var(--t-fast) var(--ease);
        }
        button.btn .ico { font-size: 16px; }
        button.btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.16);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.4);
        }
        button.btn:active:not(:disabled) { transform: translateY(0); }
        button.btn:disabled { opacity: 0.4; cursor: not-allowed; }

        button.btn.primary {
          background: linear-gradient(135deg, rgba(76,201,240,0.16), rgba(76,201,240,0.08));
          border-color: rgba(76, 201, 240, 0.32);
          color: #cfeefb;
        }
        button.btn.primary:hover:not(:disabled) {
          background: linear-gradient(135deg, rgba(76,201,240,0.24), rgba(76,201,240,0.12));
          box-shadow: 0 8px 28px -6px rgba(76, 201, 240, 0.4);
        }
        button.btn.success {
          background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(16,185,129,0.08));
          border-color: rgba(16, 185, 129, 0.32);
          color: #b6f0d6;
        }
        button.btn.success:hover:not(:disabled) {
          box-shadow: 0 8px 28px -6px rgba(16, 185, 129, 0.4);
        }
        button.btn.danger {
          background: linear-gradient(135deg, rgba(239,68,68,0.16), rgba(239,68,68,0.06));
          border-color: rgba(239, 68, 68, 0.30);
          color: #fbb4b4;
        }
        button.btn.danger:hover:not(:disabled) {
          box-shadow: 0 8px 28px -6px rgba(239, 68, 68, 0.4);
        }
        button.btn.warning {
          background: linear-gradient(135deg, rgba(244,162,97,0.16), rgba(244,162,97,0.06));
          border-color: rgba(244, 162, 97, 0.32);
          color: #f9d2a6;
        }
        button.btn.warning:hover:not(:disabled) {
          box-shadow: 0 8px 28px -6px rgba(244, 162, 97, 0.4);
        }

        /* ─────────────── TOGGLE GROUPS ─────────────── */
        .toggle-group {
          display: grid;
          gap: 4px;
          padding: 4px;
          background: rgba(0, 0, 0, 0.22);
          border: 1px solid var(--glass-border);
          border-radius: 14px;
        }
        .toggle-group.cols-3 { grid-template-columns: repeat(3, 1fr); }
        .toggle-group.cols-2 { grid-template-columns: repeat(2, 1fr); }

        .toggle-group .btn {
          padding: 10px 12px;
          background: transparent;
          border: 1px solid transparent;
          font-size: 12px;
          letter-spacing: 0.04em;
        }
        .toggle-group .btn:hover:not(.active):not(:disabled) {
          background: rgba(255, 255, 255, 0.04);
          transform: none;
          box-shadow: none;
        }
        .toggle-group .btn.active {
          background: linear-gradient(135deg, rgba(76,201,240,0.22), rgba(76,201,240,0.10));
          border-color: rgba(76, 201, 240, 0.35);
          color: #ffffff;
          box-shadow:
            0 4px 16px -4px rgba(76, 201, 240, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        .toggle-group .btn[data-season="hivernage"].active {
          background: linear-gradient(135deg, rgba(59,130,246,0.22), rgba(59,130,246,0.10));
          border-color: rgba(59, 130, 246, 0.35);
          box-shadow:
            0 4px 16px -4px rgba(59, 130, 246, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        .toggle-group .btn[data-season="saison"].active {
          background: linear-gradient(135deg, rgba(244,162,97,0.22), rgba(244,162,97,0.10));
          border-color: rgba(244, 162, 97, 0.35);
          box-shadow:
            0 4px 16px -4px rgba(244, 162, 97, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .toggle-section-label {
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: var(--secondary-text-color, #8a9ba8);
          margin: var(--gap-md) 0 var(--gap-xs);
        }

        /* ─────────────── VANNE PROMPT ─────────────── */
        #vanne-prompt-zone:not(:empty) { margin-top: var(--gap-md); }
        .vanne-prompt {
          background:
            linear-gradient(135deg, rgba(244,162,97,0.18), rgba(244,162,97,0.08));
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(244, 162, 97, 0.40);
          border-radius: var(--radius-md);
          padding: var(--gap-md);
          font-size: 13px;
          line-height: 1.5;
          display: flex; align-items: center; gap: var(--gap-sm);
          color: #f9d8b4;
          animation: vanne-pulse 2.4s var(--ease) infinite;
        }
        .vanne-prompt::before {
          content: '👉';
          font-size: 22px;
          flex-shrink: 0;
        }
        .vanne-prompt strong { color: var(--accent); font-weight: 600; }
        @keyframes vanne-pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(244, 162, 97, 0.0); }
          50%      { box-shadow: 0 0 32px -4px rgba(244, 162, 97, 0.45); }
        }

        /* ─────────────── SCHEMA ─────────────── */
        .schema-card .schema-wrap {
          margin: 0 calc(-1 * var(--gap-lg));
          padding: var(--gap-md) var(--gap-lg) 0;
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

        .pump-rotor { transform-origin: 600px 540px; }
        .running .pump-rotor { animation: rot 1.2s linear infinite; }
        @keyframes rot { to { transform: rotate(360deg); } }

        .running .water-surface { animation: wave 4s ease-in-out infinite; }
        @keyframes wave { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-2px)} }

        .status-led { fill:#7a8794; }
        .running .status-led { fill:#10b981; filter:drop-shadow(0 0 6px #10b981); }
        .backwash-active .filtre-rect { stroke: #f4a261; stroke-width: 3; }

        .schema-info {
          margin-top: var(--gap-md);
          padding-top: var(--gap-md);
          border-top: 1px solid var(--glass-border);
          font-size: 12px;
          font-weight: 500;
          letter-spacing: 0.04em;
          color: var(--secondary-text-color, #8a9ba8);
          text-align: center;
        }

        /* Respect des préférences d'accessibilité : si l'utilisateur a
           désactivé les animations, on force les cards à être visibles
           directement (sinon elles resteraient à opacity: 0) et on coupe
           la pulsation du bandeau vanne et les animations de l'eau. */
        @media (prefers-reduced-motion: reduce) {
          .card {
            opacity: 1;
            transform: none;
            animation: none;
          }
          .vanne-prompt { animation: none; }
          .running .water-particle,
          .running .pump-rotor,
          .running .water-surface { animation: none; }
        }
      </style>

      <header class="app-header">
        <button class="menu-btn" id="menu-btn" title="Menu" aria-label="Menu">☰</button>
        <div class="header-titles">
          <h1 class="header-title">🏊 Pool Control</h1>
          <span class="header-subtitle">Tableau de bord</span>
        </div>
        <span class="status-badge" id="header-badge">—</span>
      </header>

      <main class="container">

        <!-- HERO : températures + état général -->
        <section class="card area-hero">
          <div class="card-head">
            <h2 class="card-title"><span class="ico">📊</span> État général</h2>
          </div>

          <div class="hero-grid">
            <div class="stat">
              <div class="stat-label"><span>💧</span> Eau</div>
              <div class="stat-value" id="temp-water">—<span class="temp-tile-unit">°C</span></div>
            </div>
            <div class="stat air">
              <div class="stat-label"><span>🌡️</span> Air</div>
              <div class="stat-value" id="temp-air">—<span class="temp-tile-unit">°C</span></div>
            </div>
          </div>

          <div class="info-list">
            <div class="info-row">
              <span class="info-label">Statut</span>
              <span class="info-value lead" id="info-control">—</span>
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
              <span class="info-value schedule" id="info-filt-schedule">—</span>
            </div>
          </div>

          <div class="actions">
            <button class="btn warning" id="btn-reset">
              <span class="ico">🔄</span> Recalculer le planning
            </button>
          </div>
        </section>

        <!-- MODES : toggle groups -->
        <section class="card area-modes">
          <div class="card-head">
            <h2 class="card-title"><span class="ico">🎛️</span> Mode de contrôle</h2>
          </div>

          <div class="toggle-section-label">Activation</div>
          <div class="toggle-group cols-3">
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

          <div class="toggle-section-label">Saison</div>
          <div class="toggle-group cols-2">
            <button class="btn" id="btn-season" data-season="saison">
              <span class="ico">☀️</span> Saison
            </button>
            <button class="btn" id="btn-winter" data-season="hivernage">
              <span class="ico">❄️</span> Hivernage
            </button>
          </div>
        </section>

        <!-- SCHEMA hydraulique -->
        <section class="card schema-card area-schema">
          <div class="card-head">
            <h2 class="card-title"><span class="ico">🔧</span> Circuit hydraulique</h2>
            <span class="card-aside">Synoptique de filtration</span>
          </div>
          <div class="schema-wrap" id="schema-wrap">
            ${this._svgMarkup()}
          </div>
          <div class="schema-info" id="schema-info">—</div>
        </section>

        <!-- STACK : Surpresseur + Lavage -->
        <div class="area-stack">

          <section class="card">
            <div class="card-head">
              <h2 class="card-title"><span class="ico">🌀</span> Surpresseur</h2>
            </div>
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">État</span>
                <span class="info-value" id="info-booster">—</span>
              </div>
            </div>
            <div class="actions cols-2">
              <button class="btn success" id="btn-booster">
                <span class="ico">▶️</span> Démarrer
              </button>
              <button class="btn danger" id="btn-stop-booster">
                <span class="ico">⏹</span> Stop
              </button>
            </div>
          </section>

          <section class="card">
            <div class="card-head">
              <h2 class="card-title"><span class="ico">🧴</span> Lavage du filtre</h2>
            </div>
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">Étape</span>
                <span class="info-value" id="info-backwash">—</span>
              </div>
            </div>

            <div id="vanne-prompt-zone"></div>

            <div class="actions cols-2">
              <button class="btn primary" id="btn-backwash">
                <span class="ico">⏭️</span> Étape suivante
              </button>
              <button class="btn danger" id="btn-stop-backwash">
                <span class="ico">⏹</span> Stop
              </button>
            </div>
          </section>

        </div>

      </main>
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
      promptHtml = `<div class="vanne-prompt"><span>Positionnez la vanne sur <strong>LAVAGE</strong>, puis appuyez sur « Étape suivante »</span></div>`;
    else if (step === 'pos_rincage')
      promptHtml = `<div class="vanne-prompt"><span>Positionnez la vanne sur <strong>RINÇAGE</strong>, puis appuyez sur « Étape suivante »</span></div>`;
    else if (step === 'pos_filtration')
      promptHtml = `<div class="vanne-prompt"><span>Repositionnez la vanne sur <strong>FILTRATION</strong>, puis appuyez sur « Étape suivante »</span></div>`;
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
      <svg class="pool-svg stopped" viewBox="0 0 1200 720" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <!-- Eau du bassin -->
          <linearGradient id="wG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#90e0ef" stop-opacity="0.95"/>
            <stop offset="50%" stop-color="#4cc9f0" stop-opacity="0.85"/>
            <stop offset="100%" stop-color="#277da1"/>
          </linearGradient>
          <!-- Carrelage bassin -->
          <linearGradient id="tG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#244e6e"/>
            <stop offset="100%" stop-color="#1a3a52"/>
          </linearGradient>
          <!-- Sol local technique -->
          <linearGradient id="floorG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1f2937"/>
            <stop offset="100%" stop-color="#0f172a"/>
          </linearGradient>
          <!-- Métal pompe / vanne -->
          <linearGradient id="mG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#4b5563"/>
            <stop offset="50%" stop-color="#374151"/>
            <stop offset="100%" stop-color="#1f2937"/>
          </linearGradient>
          <!-- Cuve filtre à sable beige -->
          <linearGradient id="fG" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#a08a6a"/>
            <stop offset="50%" stop-color="#c8b48f"/>
            <stop offset="100%" stop-color="#8c7656"/>
          </linearGradient>
          <!-- Boîtier doseur pH (bleu) -->
          <linearGradient id="phG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3b82f6"/>
            <stop offset="100%" stop-color="#1d4ed8"/>
          </linearGradient>
          <!-- Boîtier doseur chlore (jaune/safran) -->
          <linearGradient id="clG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#fbbf24"/>
            <stop offset="100%" stop-color="#d97706"/>
          </linearGradient>
          <!-- Bidon plastique blanc -->
          <linearGradient id="bottleG" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#e5e7eb"/>
            <stop offset="50%" stop-color="#f3f4f6"/>
            <stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
          <!-- Tuyau PVC -->
          <linearGradient id="pipeG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#475569"/>
            <stop offset="50%" stop-color="#334155"/>
            <stop offset="100%" stop-color="#1e293b"/>
          </linearGradient>
        </defs>

        <!-- LED status (haut droite) -->
        <circle class="status-led" cx="1160" cy="30" r="6"/>
        <text id="status-led-text" x="1145" y="34" text-anchor="end"
              font-family="Georgia,serif" font-size="11" fill="#8a9ba8"
              letter-spacing="0.1em">À L'ARRÊT</text>

        <!-- Sol du local technique -->
        <rect x="0" y="500" width="1200" height="220" fill="url(#floorG)"/>
        <line x1="0" y1="500" x2="1200" y2="500" stroke="#4b5563" stroke-width="1" opacity="0.5"/>

        <!-- ───────── BASSIN (vue en coupe) ───────── -->
        <!-- Margelle / bord supérieur -->
        <rect x="20" y="100" width="430" height="14" fill="#9aa8b5" rx="2"/>
        <!-- Cuve du bassin (carrelage) -->
        <path d="M 30,114 L 30,380 Q 30,395 45,395 L 425,395 Q 440,395 440,380 L 440,114 Z" fill="url(#tG)"/>
        <!-- Eau -->
        <path d="M 42,128 L 42,378 Q 42,383 47,383 L 423,383 Q 428,383 428,378 L 428,128 Z" fill="url(#wG)"/>
        <!-- Surface ondulée -->
        <g class="water-surface">
          <path d="M 42,138 Q 80,132 120,138 T 200,138 T 280,138 T 360,138 T 428,138"
                stroke="#caf0f8" stroke-width="1.2" fill="none" opacity="0.85"/>
        </g>

        <!-- Skimmer (boîte sur le bord droit) -->
        <rect x="380" y="120" width="50" height="60" fill="#f3f4f6" stroke="#9aa8b5" stroke-width="1.5" rx="2"/>
        <rect x="384" y="124" width="42" height="6" fill="#cbd5e1"/>
        <rect x="395" y="135" width="20" height="40" fill="#0b1620"/>

        <!-- Bonde de fond (grille au sol du bassin) -->
        <ellipse cx="120" cy="385" rx="32" ry="6" fill="#9aa8b5" stroke="#475569" stroke-width="1.5"/>
        <line x1="92" y1="385" x2="148" y2="385" stroke="#475569" stroke-width="1"/>
        <line x1="100" y1="383" x2="140" y2="383" stroke="#475569" stroke-width="0.5" opacity="0.6"/>

        <!-- Refoulement (buse de retour eau, bord gauche bassin) -->
        <rect x="34" y="180" width="14" height="22" fill="#374151" stroke="#1f2937" stroke-width="1"/>
        <circle cx="36" cy="191" r="4" fill="#0b1620"/>

        <!-- ───────── TUYAUTERIE PVC ───────── -->
        <g stroke="#1e293b" stroke-width="1">
          <!-- Aspiration : skimmer → pompe -->
          <rect x="410" y="180" width="16" height="280" fill="url(#pipeG)"/>
          <rect x="410" y="450" width="120" height="16" fill="url(#pipeG)"/>
          <rect x="514" y="450" width="16" height="120" fill="url(#pipeG)"/>
          <!-- Aspiration : bonde de fond → rejoint la canalisation principale -->
          <path d="M 120,395 L 120,460 L 410,460" fill="none" stroke="url(#pipeG)" stroke-width="14" stroke-linecap="round"/>
          <!-- Pompe → filtre -->
          <rect x="635" y="420" width="16" height="120" fill="url(#pipeG)"/>
          <rect x="635" y="420" width="160" height="16" fill="url(#pipeG)"/>
          <rect x="780" y="280" width="16" height="155" fill="url(#pipeG)"/>
          <!-- Filtre → doseurs (en hauteur) -->
          <rect x="860" y="270" width="80" height="14" fill="url(#pipeG)"/>
          <rect x="930" y="218" width="14" height="60" fill="url(#pipeG)"/>
          <rect x="940" y="218" width="225" height="14" fill="url(#pipeG)"/>
          <!-- Retour bassin (refoulement) -->
          <rect x="1156" y="218" width="14" height="438" fill="url(#pipeG)"/>
          <rect x="48" y="650" width="1115" height="14" fill="url(#pipeG)"/>
          <rect x="48" y="200" width="14" height="455" fill="url(#pipeG)"/>
          <!-- Coude vers la buse de refoulement -->
          <path d="M 55,200 L 55,191 L 48,191" fill="none" stroke="url(#pipeG)" stroke-width="14"/>
        </g>

        <!-- ───────── POMPE (#2) ───────── -->
        <!-- Moteur arrière -->
        <rect x="650" y="500" width="80" height="80" rx="6" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="690" cy="540" r="6" fill="#0b1620"/>
        <!-- Corps de pompe (volute) -->
        <ellipse cx="600" cy="540" rx="60" ry="50" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="600" cy="540" rx="42" ry="34" fill="#1f2937"/>
        <!-- Rotor animé -->
        <g class="pump-rotor">
          <circle cx="600" cy="540" r="30" fill="#111827"/>
          <path d="M 600,514 Q 614,540 600,566 Q 586,540 600,514" fill="#9ca3af"/>
          <path d="M 574,540 Q 600,526 626,540 Q 600,554 574,540" fill="#9ca3af"/>
          <circle cx="600" cy="540" r="5" fill="#f4a261"/>
        </g>
        <!-- Préfiltre / panier de pompe -->
        <rect x="544" y="558" width="40" height="34" rx="3" fill="url(#mG)" stroke="#0b1620"/>
        <rect x="548" y="566" width="32" height="20" fill="#1f2937" opacity="0.8"/>

        <!-- ───────── FILTRE À SABLE (#3) ───────── -->
        <!-- Vanne 6 voies (au sommet) -->
        <ellipse cx="820" cy="278" rx="44" ry="10" fill="url(#mG)"/>
        <rect x="776" y="240" width="88" height="40" rx="6" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="820" cy="240" rx="44" ry="10" fill="#4b5563" stroke="#0b1620" stroke-width="1"/>
        <!-- Manette latérale -->
        <rect x="820" y="218" width="60" height="6" rx="3" fill="#0b1620"/>
        <circle cx="884" cy="221" r="6" fill="#1f2937" stroke="#0b1620"/>
        <circle cx="820" cy="240" r="5" fill="#f4a261"/>
        <!-- Cuve filtre -->
        <ellipse cx="820" cy="290" rx="56" ry="14" fill="url(#fG)" stroke="#0b1620" stroke-width="1"/>
        <rect class="filtre-rect" x="764" y="290" width="112" height="220" fill="url(#fG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="820" cy="510" rx="56" ry="14" fill="#8c7656" stroke="#0b1620" stroke-width="1.5"/>
        <!-- Pied / socle -->
        <rect x="780" y="510" width="80" height="22" rx="3" fill="#1f2937" stroke="#0b1620"/>
        <!-- Niveau de sable interne (légèrement transparent) -->
        <rect x="770" y="370" width="100" height="130" fill="#a08a6a" opacity="0.55"/>

        <!-- ───────── DOSEUR pH (#4) ───────── -->
        <!-- Boîtier -->
        <rect x="930" y="160" width="80" height="80" rx="8" fill="url(#phG)" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="970" cy="200" r="22" fill="#1e3a8a" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="970" cy="200" r="14" fill="#1d4ed8"/>
        <circle cx="970" cy="200" r="3" fill="#bfdbfe"/>
        <!-- Tube vers bidon -->
        <line x1="970" y1="240" x2="970" y2="320" stroke="#3b82f6" stroke-width="3"/>
        <!-- Bidon pH -->
        <ellipse cx="970" cy="320" rx="32" ry="8" fill="#cbd5e1"/>
        <rect x="938" y="320" width="64" height="120" fill="url(#bottleG)" stroke="#94a3b8" stroke-width="1"/>
        <ellipse cx="970" cy="440" rx="32" ry="8" fill="#94a3b8"/>
        <rect x="950" y="305" width="40" height="20" rx="3" fill="#cbd5e1" stroke="#94a3b8"/>
        <rect x="945" y="365" width="50" height="30" rx="2" fill="#fff"/>
        <text x="970" y="386" text-anchor="middle" font-family="'Inter', system-ui, sans-serif"
              font-size="14" font-weight="700" fill="#1e293b">pH</text>

        <!-- ───────── DOSEUR CHLORE (#5) ───────── -->
        <!-- Boîtier -->
        <rect x="1090" y="160" width="80" height="80" rx="8" fill="url(#clG)" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="1130" cy="200" r="22" fill="#92400e" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="1130" cy="200" r="14" fill="#d97706"/>
        <circle cx="1130" cy="200" r="3" fill="#fef3c7"/>
        <!-- Tube vers bidon -->
        <line x1="1130" y1="240" x2="1130" y2="320" stroke="#fbbf24" stroke-width="3"/>
        <!-- Bidon Chlore -->
        <ellipse cx="1130" cy="320" rx="32" ry="8" fill="#cbd5e1"/>
        <rect x="1098" y="320" width="64" height="120" fill="url(#bottleG)" stroke="#94a3b8" stroke-width="1"/>
        <ellipse cx="1130" cy="440" rx="32" ry="8" fill="#94a3b8"/>
        <rect x="1110" y="305" width="40" height="20" rx="3" fill="#cbd5e1" stroke="#94a3b8"/>
        <rect x="1098" y="365" width="64" height="30" rx="2" fill="#fff"/>
        <text x="1130" y="386" text-anchor="middle" font-family="'Inter', system-ui, sans-serif"
              font-size="13" font-weight="700" fill="#1e293b">Chlore</text>

        <!-- ───────── FLÈCHES D'ÉCOULEMENT ───────── -->
        <!-- Aspiration : skimmer → pompe -->
        <g class="flow-asp">
          ${[1,2,3,4,5,6,7,8].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 418,200 L 418,458 L 522,458 L 522,565')"/>`
          ).join('')}
        </g>
        <!-- Pompe → filtre -->
        <g class="flow-pf">
          ${[1,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 643,520 L 643,428 L 788,428 L 788,290')"/>`
          ).join('')}
        </g>
        <!-- Filtre → doseurs → tuyau retour -->
        <g class="flow-fr">
          ${[1,2,3,4,5,6,7,8].map(i =>
            `<circle class="water-particle p${i}" r="2.8"
             style="offset-path: path('M 866,277 L 937,277 L 937,225 L 1163,225')"/>`
          ).join('')}
        </g>
        <!-- Refoulement : retour au bassin -->
        <g class="flow-ret">
          ${[1,2,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 1163,232 L 1163,657 L 55,657 L 55,193')"/>`
          ).join('')}
        </g>

        <!-- ───────── NUMÉROS (badges sur les éléments) ───────── -->
        <g font-family="'Inter', system-ui, sans-serif" font-size="13" font-weight="700">
          <circle cx="395" cy="105" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="395" y="110" text-anchor="middle" fill="#0b1620">1</text>
          <circle cx="600" cy="478" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="600" y="483" text-anchor="middle" fill="#0b1620">2</text>
          <circle cx="820" cy="200" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="820" y="205" text-anchor="middle" fill="#0b1620">3</text>
          <circle cx="970" cy="135" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="970" y="140" text-anchor="middle" fill="#0b1620">4</text>
          <circle cx="1130" cy="135" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="1130" y="140" text-anchor="middle" fill="#0b1620">5</text>
          <circle cx="55" cy="160" r="14" fill="#f4a261" stroke="#0b1620" stroke-width="1.5"/>
          <text x="55" y="165" text-anchor="middle" fill="#0b1620">6</text>
        </g>

        <!-- ───────── LABELS CHIPS ───────── -->
        <g font-family="'Inter', system-ui, sans-serif" font-size="11" font-weight="500">
          <!-- Skimmer -->
          <rect x="450" y="135" width="78" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="489" y="150" text-anchor="middle" fill="#e2e8f0">Skimmer</text>
          <!-- Bonde de fond -->
          <rect x="55" y="408" width="120" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="115" y="423" text-anchor="middle" fill="#e2e8f0">Bonde de fond</text>
          <!-- Pompe -->
          <rect x="668" y="610" width="60" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="698" y="625" text-anchor="middle" fill="#e2e8f0">Pompe</text>
          <!-- Filtre à sable -->
          <rect x="755" y="334" width="130" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="820" y="349" text-anchor="middle" fill="#e2e8f0">Filtre à sable</text>
          <!-- Traitement pH -->
          <rect x="918" y="125" width="104" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="970" y="140" text-anchor="middle" fill="#e2e8f0">Traitement pH</text>
          <!-- Traitement chlore -->
          <rect x="1070" y="125" width="120" height="22" rx="4" fill="#1e293b" stroke="#475569"/>
          <text x="1130" y="140" text-anchor="middle" fill="#e2e8f0">Traitement chlore</text>
        </g>

        <!-- Sigles BASSIN / LOCAL TECHNIQUE -->
        <text x="225" y="80" text-anchor="middle" font-family="Georgia,serif"
              font-size="11" fill="#f4a261" letter-spacing="0.18em">BASSIN</text>
        <text x="800" y="80" text-anchor="middle" font-family="Georgia,serif"
              font-size="10" fill="#8a9ba8" letter-spacing="0.18em">LOCAL TECHNIQUE</text>

        <!-- ───────── LÉGENDE EN BAS À GAUCHE ───────── -->
        <g font-family="'Inter', system-ui, sans-serif">
          <rect x="20" y="528" width="280" height="160" rx="8"
                fill="#0b1620" stroke="#1e293b" stroke-width="1" opacity="0.92"/>
          <g font-size="12" fill="#e2e8f0">
            <circle cx="42" cy="552" r="9" fill="#f4a261"/><text x="42" y="557" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">1</text>
            <text x="60" y="557">Skimmer + Bonde de fond</text>

            <circle cx="42" cy="578" r="9" fill="#f4a261"/><text x="42" y="583" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">2</text>
            <text x="60" y="583">Pompe</text>

            <circle cx="42" cy="604" r="9" fill="#f4a261"/><text x="42" y="609" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">3</text>
            <text x="60" y="609">Filtre à sable</text>

            <circle cx="42" cy="630" r="9" fill="#f4a261"/><text x="42" y="635" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">4</text>
            <text x="60" y="635">Traitement pH</text>

            <circle cx="42" cy="656" r="9" fill="#f4a261"/><text x="42" y="661" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">5</text>
            <text x="60" y="661">Traitement chlore</text>

            <circle cx="42" cy="682" r="9" fill="#f4a261"/><text x="42" y="687" text-anchor="middle" font-size="11" font-weight="700" fill="#0b1620">6</text>
            <text x="60" y="687">Refoulement</text>
          </g>
        </g>
      </svg>
    `;
  }
}

customElements.define('pool-control-panel', PoolControlPanel);
