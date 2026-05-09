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
    this._heatPumpEntity = null;
    this._instancePrefix = 'pool_control';
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      const cfg = (this.panel && this.panel.config) || {};
      if (cfg.water_entity) this._waterTempEntity = cfg.water_entity;
      if (cfg.air_entity) this._airTempEntity = cfg.air_entity;
      if (cfg.heat_pump_entity) this._heatPumpEntity = cfg.heat_pump_entity;
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

  _isHeatPumpRunning() {
    if (!this._heatPumpEntity) return false;
    const st = this._entityState(this._heatPumpEntity);
    if (!st) return false;

    // Pour une entité climate, le state correspond au hvac_mode
    // (heat / cool / off) et reste à "heat" même quand la PAC est idle.
    // On lit donc en priorité attributes.hvac_action qui distingue
    // heating / cooling / idle / off.
    if (this._heatPumpEntity.startsWith('climate.')) {
      const action = (st.attributes && st.attributes.hvac_action) || '';
      if (action) {
        return /^(heating|cooling|drying|fan)$/i.test(action);
      }
      // Fallback : state ≠ off / unknown / unavailable
      return !/^(off|unknown|unavailable)$/i.test(st.state);
    }

    // switch / input_boolean : on / off explicite
    return /^on$/i.test(st.state);
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

        /* fill-box + center : évite les coordonnées magiques quand le SVG bouge */
        .pump-rotor { transform-box: fill-box; transform-origin: center; }
        .running .pump-rotor { animation: rot 1.2s linear infinite; }
        @keyframes rot { to { transform: rotate(360deg); } }

        /* Pompe à chaleur : ventilateur frontal + flux dérivé via by-pass */
        .pac-rotor { transform-box: fill-box; transform-origin: center; }
        .heat-pump-active .pac-rotor { animation: rot 1.6s linear infinite; }
        .pac-housing { opacity: 0.55; }
        .heat-pump-configured .pac-housing { opacity: 1; }
        .flow-pac .water-particle { opacity: 0; }
        .heat-pump-active .flow-pac .water-particle { opacity: 1; animation: flowPac 4s linear infinite; }
        @keyframes flowPac { from{offset-distance:0%} to{offset-distance:100%} }
        .running:not(.heat-pump-active) .flow-bypass .water-particle { opacity: 1; animation: flowBypass 3.5s linear infinite; }
        .running.heat-pump-active .flow-bypass .water-particle { opacity: 0; }
        .stopped .flow-bypass .water-particle { opacity: 0; }
        @keyframes flowBypass { from{offset-distance:0%} to{offset-distance:100%} }

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
          .running .water-surface,
          .heat-pump-active .pac-rotor,
          .heat-pump-active .flow-pac .water-particle,
          .running .flow-bypass .water-particle { animation: none; }
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
      svg.classList.toggle('heat-pump-active', running && this._isHeatPumpRunning());
      svg.classList.toggle('heat-pump-configured', !!this._heatPumpEntity);
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
      <svg class="pool-svg stopped" viewBox="0 0 1400 960" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="wG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#90e0ef" stop-opacity="0.95"/>
            <stop offset="50%" stop-color="#4cc9f0" stop-opacity="0.85"/>
            <stop offset="100%" stop-color="#277da1"/>
          </linearGradient>
          <linearGradient id="tG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#244e6e"/>
            <stop offset="100%" stop-color="#1a3a52"/>
          </linearGradient>
          <linearGradient id="floorG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#d6cdb8"/>
            <stop offset="100%" stop-color="#a8a08c"/>
          </linearGradient>
          <linearGradient id="wallG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#e8e0c9"/>
            <stop offset="100%" stop-color="#bfb59d"/>
          </linearGradient>
          <linearGradient id="mG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#4b5563"/>
            <stop offset="50%" stop-color="#374151"/>
            <stop offset="100%" stop-color="#1f2937"/>
          </linearGradient>
          <linearGradient id="fG" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#a08a6a"/>
            <stop offset="50%" stop-color="#c8b48f"/>
            <stop offset="100%" stop-color="#8c7656"/>
          </linearGradient>
          <linearGradient id="phG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#3b82f6"/>
            <stop offset="100%" stop-color="#1d4ed8"/>
          </linearGradient>
          <linearGradient id="clG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#fbbf24"/>
            <stop offset="100%" stop-color="#d97706"/>
          </linearGradient>
          <linearGradient id="bottleG" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#e5e7eb"/>
            <stop offset="50%" stop-color="#f3f4f6"/>
            <stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
          <linearGradient id="pipeG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#475569"/>
            <stop offset="50%" stop-color="#334155"/>
            <stop offset="100%" stop-color="#1e293b"/>
          </linearGradient>
          <linearGradient id="pacG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#f3f4f6"/>
            <stop offset="100%" stop-color="#cbd5e1"/>
          </linearGradient>
        </defs>

        <!-- LED status -->
        <circle class="status-led" cx="1360" cy="30" r="6"/>
        <text id="status-led-text" x="1345" y="34" text-anchor="end"
              font-family="Georgia,serif" font-size="11" fill="#8a9ba8"
              letter-spacing="0.1em">À L'ARRÊT</text>

        <!-- Mur du fond (béton beige) -->
        <rect x="100" y="80" width="1080" height="540" fill="url(#wallG)"/>
        <line x1="100" y1="80" x2="1180" y2="80" stroke="#9a8f6c" stroke-width="1.5"/>
        <line x1="100" y1="620" x2="1180" y2="620" stroke="#7a7058" stroke-width="2"/>

        <!-- Sol carrelé du local technique -->
        <rect x="100" y="620" width="1080" height="160" fill="url(#floorG)"/>
        ${Array.from({length:9}, (_,i) =>
          `<line x1="${100+i*120}" y1="620" x2="${100+i*120}" y2="780" stroke="#9a917b" stroke-width="0.7" opacity="0.5"/>`
        ).join('')}
        <line x1="100" y1="700" x2="1180" y2="700" stroke="#9a917b" stroke-width="0.7" opacity="0.5"/>

        <!-- Réglette néon au plafond -->
        <rect x="600" y="105" width="320" height="14" rx="4" fill="#fafaf5" stroke="#94a3b8" stroke-width="1"/>
        <rect x="610" y="108" width="300" height="6" fill="#fef9c3" opacity="0.9"/>

        <!-- Coffret électrique mural -->
        <rect x="200" y="180" width="120" height="180" rx="6" fill="#f3f4f6" stroke="#94a3b8" stroke-width="1.5"/>
        <rect x="220" y="200" width="80" height="60" rx="2" fill="#0b1620"/>
        <rect x="226" y="208" width="68" height="42" fill="#1e3a8a"/>
        <rect x="226" y="252" width="40" height="3" fill="#10b981"/>
        <circle cx="240" cy="290" r="6" fill="#10b981"/>
        <circle cx="260" cy="290" r="6" fill="#374151"/>
        <circle cx="280" cy="290" r="6" fill="#374151"/>
        <rect x="220" y="310" width="80" height="40" rx="2" fill="#e5e7eb" stroke="#94a3b8"/>

        <!-- ───────── BASSIN (vue en coupe à gauche) ───────── -->
        <rect x="0" y="540" width="280" height="14" fill="#9aa8b5" rx="2"/>
        <path d="M 10,554 L 10,860 Q 10,876 26,876 L 264,876 Q 280,876 280,860 L 280,554 Z" fill="url(#tG)"/>
        <path d="M 22,568 L 22,858 Q 22,864 28,864 L 262,864 Q 268,864 268,858 L 268,568 Z" fill="url(#wG)"/>
        <g class="water-surface">
          <path d="M 22,580 Q 60,572 100,580 T 178,580 T 256,580 T 268,580"
                stroke="#caf0f8" stroke-width="1.4" fill="none" opacity="0.85"/>
        </g>

        <!-- Skimmer (#1) sur le bord droit du bassin -->
        <rect x="240" y="558" width="36" height="46" fill="#f3f4f6" stroke="#9aa8b5" stroke-width="1.5" rx="2"/>
        <rect x="244" y="562" width="28" height="4" fill="#cbd5e1"/>
        <rect x="252" y="572" width="14" height="30" fill="#0b1620"/>

        <!-- Bonde de fond (#2) au sol du bassin -->
        <ellipse cx="140" cy="864" rx="32" ry="6" fill="#9aa8b5" stroke="#475569" stroke-width="1.5"/>
        <line x1="112" y1="864" x2="168" y2="864" stroke="#475569" stroke-width="1"/>
        <line x1="120" y1="862" x2="160" y2="862" stroke="#475569" stroke-width="0.5" opacity="0.6"/>

        <!-- Buse de retour piscine (#8) - haut gauche du bassin -->
        <rect x="14" y="640" width="14" height="22" fill="#374151" stroke="#1f2937" stroke-width="1"/>
        <circle cx="16" cy="651" r="4" fill="#0b1620"/>

        <!-- ───────── TUYAUTERIE PVC (rectangles avec gradient) ───────── -->
        <g stroke="#1e293b" stroke-width="1">
          <!-- Aspiration : skimmer → tuyau au sol → pompe -->
          <rect x="251" y="604" width="14" height="92" fill="url(#pipeG)"/>
          <rect x="251" y="690" width="200" height="14" fill="url(#pipeG)"/>
          <rect x="437" y="690" width="14" height="34" fill="url(#pipeG)"/>
          <!-- Aspiration : bonde de fond → rejoint -->
          <rect x="133" y="800" width="14" height="40" fill="url(#pipeG)"/>
          <rect x="133" y="800" width="180" height="14" fill="url(#pipeG)"/>
          <rect x="299" y="700" width="14" height="100" fill="url(#pipeG)"/>
          <!-- Pompe → filtre (côté haut) -->
          <rect x="540" y="640" width="14" height="56" fill="url(#pipeG)"/>
          <rect x="423" y="640" width="131" height="14" fill="url(#pipeG)"/>
          <rect x="423" y="450" width="14" height="200" fill="url(#pipeG)"/>
          <!-- Filtre → entrée by-pass -->
          <rect x="437" y="430" width="220" height="14" fill="url(#pipeG)"/>
          <!-- By-pass droite (court-circuit horizontal) -->
          <rect x="643" y="430" width="180" height="14" fill="url(#pipeG)"/>
          <!-- By-pass bas (vers PAC) -->
          <rect x="643" y="430" width="14" height="160" fill="url(#pipeG)"/>
          <rect x="643" y="576" width="500" height="14" fill="url(#pipeG)"/>
          <rect x="809" y="430" width="14" height="160" fill="url(#pipeG)"/>
          <rect x="1129" y="430" width="14" height="160" fill="url(#pipeG)"/>
          <rect x="809" y="576" width="334" height="14" fill="url(#pipeG)"/>
          <!-- Sondes (segment horizontal après by-pass) -->
          <rect x="809" y="430" width="380" height="14" fill="url(#pipeG)"/>
          <!-- Retour piscine (#8) -->
          <rect x="1175" y="430" width="14" height="280" fill="url(#pipeG)"/>
          <rect x="20" y="700" width="1169" height="14" fill="url(#pipeG)"/>
          <rect x="20" y="660" width="14" height="54" fill="url(#pipeG)"/>
        </g>

        <!-- Vannes by-pass (vannes à boule bleues stylisées) -->
        <g stroke="#0b1620" stroke-width="1.5">
          <circle cx="730" cy="437" r="13" fill="#3b82f6"/>
          <rect x="725" y="424" width="10" height="6" fill="#1e3a8a"/>
          <circle cx="730" cy="583" r="13" fill="#3b82f6"/>
          <rect x="725" y="570" width="10" height="6" fill="#1e3a8a"/>
        </g>
        <text x="730" y="510" text-anchor="middle" font-family="'Inter', system-ui, sans-serif"
              font-size="9" font-weight="600" fill="#475569" letter-spacing="0.08em">BY-PASS</text>

        <!-- ───────── FILTRE À SABLE (#4) ───────── -->
        <ellipse cx="380" cy="358" rx="44" ry="10" fill="url(#mG)"/>
        <rect x="336" y="320" width="88" height="40" rx="6" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="380" cy="320" rx="44" ry="10" fill="#4b5563" stroke="#0b1620" stroke-width="1"/>
        <rect x="380" y="298" width="60" height="6" rx="3" fill="#0b1620"/>
        <circle cx="444" cy="301" r="6" fill="#1f2937" stroke="#0b1620"/>
        <circle cx="380" cy="320" r="5" fill="#f4a261"/>
        <ellipse cx="380" cy="370" rx="56" ry="14" fill="url(#fG)" stroke="#0b1620" stroke-width="1"/>
        <rect class="filtre-rect" x="324" y="370" width="112" height="180" fill="url(#fG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="380" cy="550" rx="56" ry="14" fill="#8c7656" stroke="#0b1620" stroke-width="1.5"/>
        <rect x="340" y="550" width="80" height="22" rx="3" fill="#1f2937" stroke="#0b1620"/>
        <rect x="330" y="430" width="100" height="100" fill="#a08a6a" opacity="0.55"/>

        <!-- ───────── POMPE (#3) ───────── -->
        <rect x="500" y="660" width="80" height="80" rx="6" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="540" cy="700" r="6" fill="#0b1620"/>
        <ellipse cx="450" cy="700" rx="60" ry="50" fill="url(#mG)" stroke="#0b1620" stroke-width="1.5"/>
        <ellipse cx="450" cy="700" rx="42" ry="34" fill="#1f2937"/>
        <g class="pump-rotor">
          <circle cx="450" cy="700" r="30" fill="#111827"/>
          <path d="M 450,674 Q 464,700 450,726 Q 436,700 450,674" fill="#9ca3af"/>
          <path d="M 424,700 Q 450,686 476,700 Q 450,714 424,700" fill="#9ca3af"/>
          <circle cx="450" cy="700" r="5" fill="#f4a261"/>
        </g>
        <rect x="394" y="718" width="40" height="34" rx="3" fill="url(#mG)" stroke="#0b1620"/>
        <rect x="398" y="726" width="32" height="20" fill="#1f2937" opacity="0.8"/>

        <!-- ───────── DOSEUR pH MURAL (#6) ───────── -->
        <rect x="850" y="180" width="100" height="100" rx="8" fill="url(#phG)" stroke="#0b1620" stroke-width="1.5"/>
        <rect x="860" y="190" width="80" height="32" rx="2" fill="#0b1620"/>
        <rect x="864" y="194" width="72" height="24" fill="#1e3a8a"/>
        <text x="900" y="210" text-anchor="middle" font-family="'Inter', monospace" font-size="11" font-weight="700" fill="#bfdbfe">pH</text>
        <circle cx="900" cy="252" r="18" fill="#1e3a8a" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="900" cy="252" r="11" fill="#1d4ed8"/>
        <circle cx="900" cy="252" r="3" fill="#bfdbfe"/>
        <line x1="900" y1="280" x2="900" y2="350" stroke="#3b82f6" stroke-width="3"/>

        <!-- Bidon pH -->
        <ellipse cx="900" cy="350" rx="32" ry="8" fill="#cbd5e1"/>
        <rect x="868" y="350" width="64" height="100" fill="url(#bottleG)" stroke="#94a3b8" stroke-width="1"/>
        <ellipse cx="900" cy="450" rx="32" ry="8" fill="#94a3b8"/>
        <rect x="880" y="335" width="40" height="20" rx="3" fill="#cbd5e1" stroke="#94a3b8"/>
        <rect x="870" y="380" width="60" height="36" rx="2" fill="#fff" stroke="#94a3b8"/>
        <rect x="876" y="386" width="20" height="24" rx="2" fill="#3b82f6"/>
        <text x="886" y="404" text-anchor="middle" font-family="'Inter', system-ui, sans-serif"
              font-size="13" font-weight="700" fill="#fff">pH</text>

        <!-- Sonde pH dans le tuyau (tube vertical) -->
        <rect x="892" y="395" width="16" height="50" fill="#0b1620" stroke="#1f2937" stroke-width="1"/>
        <rect x="888" y="395" width="24" height="6" rx="2" fill="#374151"/>
        <line x1="900" y1="445" x2="900" y2="430" stroke="#1e293b" stroke-width="2"/>

        <!-- ───────── DOSEUR CHLORE MURAL (#7) ───────── -->
        <rect x="990" y="180" width="100" height="100" rx="8" fill="url(#clG)" stroke="#0b1620" stroke-width="1.5"/>
        <rect x="1000" y="190" width="80" height="32" rx="2" fill="#0b1620"/>
        <rect x="1004" y="194" width="72" height="24" fill="#92400e"/>
        <text x="1040" y="210" text-anchor="middle" font-family="'Inter', monospace" font-size="11" font-weight="700" fill="#fef3c7">CL</text>
        <circle cx="1040" cy="252" r="18" fill="#92400e" stroke="#0b1620" stroke-width="1.5"/>
        <circle cx="1040" cy="252" r="11" fill="#d97706"/>
        <circle cx="1040" cy="252" r="3" fill="#fef3c7"/>
        <line x1="1040" y1="280" x2="1040" y2="350" stroke="#fbbf24" stroke-width="3"/>

        <!-- Bidon Chlore -->
        <ellipse cx="1040" cy="350" rx="32" ry="8" fill="#cbd5e1"/>
        <rect x="1008" y="350" width="64" height="100" fill="url(#bottleG)" stroke="#94a3b8" stroke-width="1"/>
        <ellipse cx="1040" cy="450" rx="32" ry="8" fill="#94a3b8"/>
        <rect x="1020" y="335" width="40" height="20" rx="3" fill="#cbd5e1" stroke="#94a3b8"/>
        <rect x="1010" y="380" width="60" height="36" rx="2" fill="#fff" stroke="#94a3b8"/>
        <rect x="1016" y="386" width="20" height="24" rx="2" fill="#fbbf24"/>
        <text x="1026" y="404" text-anchor="middle" font-family="'Inter', system-ui, sans-serif"
              font-size="11" font-weight="700" fill="#0b1620">CL</text>

        <!-- Sonde Chlore dans le tuyau (tube vertical) -->
        <rect x="1032" y="395" width="16" height="50" fill="#0b1620" stroke="#1f2937" stroke-width="1"/>
        <rect x="1028" y="395" width="24" height="6" rx="2" fill="#374151"/>

        <!-- ───────── POMPE À CHALEUR (#5) à l'extérieur droite ───────── -->
        <g class="pac-housing">
          <rect x="1230" y="500" width="160" height="160" rx="6" fill="url(#pacG)" stroke="#0b1620" stroke-width="1.5"/>
          <rect x="1230" y="500" width="160" height="20" rx="6" fill="#94a3b8"/>
          <rect x="1238" y="528" width="6" height="124" fill="#94a3b8"/>
          <rect x="1376" y="528" width="6" height="124" fill="#94a3b8"/>
          <!-- Grille frontale -->
          <circle cx="1310" cy="585" r="55" fill="#0b1620" stroke="#475569" stroke-width="1.5"/>
          <circle cx="1310" cy="585" r="50" fill="#1f2937"/>
          <!-- Hélice -->
          <g class="pac-rotor">
            <circle cx="1310" cy="585" r="12" fill="#374151" stroke="#0b1620"/>
            <path d="M 1310,535 Q 1325,565 1310,585 Q 1295,565 1310,535" fill="#94a3b8" opacity="0.85"/>
            <path d="M 1260,585 Q 1290,600 1310,585 Q 1290,570 1260,585" fill="#94a3b8" opacity="0.85"/>
            <path d="M 1310,635 Q 1295,605 1310,585 Q 1325,605 1310,635" fill="#94a3b8" opacity="0.85"/>
            <path d="M 1360,585 Q 1330,570 1310,585 Q 1330,600 1360,585" fill="#94a3b8" opacity="0.85"/>
            <circle cx="1310" cy="585" r="5" fill="#f4a261"/>
          </g>
          <!-- Pied -->
          <rect x="1240" y="660" width="140" height="14" rx="2" fill="#374151"/>
        </g>
        <!-- Galets / extérieur (suggéré) -->
        <rect x="1180" y="700" width="220" height="60" fill="#a8a08c" opacity="0.6"/>
        ${Array.from({length:18}, () => {
          const x = 1190 + Math.floor(Math.random()*200);
          const y = 710 + Math.floor(Math.random()*40);
          const r = 3 + Math.floor(Math.random()*4);
          return `<circle cx="${x}" cy="${y}" r="${r}" fill="#7a7058" opacity="0.55"/>`;
        }).join('')}

        <!-- ───────── FLÈCHES D'ÉCOULEMENT ───────── -->
        <!-- Aspiration : skimmer + bonde → pompe -->
        <g class="flow-asp">
          ${[1,2,3,4,5,6,7,8].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 258,604 L 258,696 L 444,696 L 444,705')"/>`
          ).join('')}
        </g>
        <!-- Pompe → filtre (côté haut) -->
        <g class="flow-pf">
          ${[1,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 510,668 L 547,668 L 547,640 L 430,640 L 430,360')"/>`
          ).join('')}
        </g>
        <!-- Filtre → vanne by-pass (entrée du nœud) -->
        <g class="flow-fr">
          ${[1,2,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="2.8"
             style="offset-path: path('M 437,437 L 720,437')"/>`
          ).join('')}
        </g>
        <!-- By-pass court-circuit (PAC inactive) -->
        <g class="flow-bypass">
          ${[1,3,5,7].map(i =>
            `<circle class="water-particle p${i}" r="2.6"
             style="offset-path: path('M 740,437 L 1180,437')"/>`
          ).join('')}
        </g>
        <!-- By-pass via PAC (PAC active) -->
        <g class="flow-pac">
          ${[1,2,3,4,5,6,7].map(i =>
            `<circle class="water-particle p${i}" r="2.8"
             style="offset-path: path('M 650,437 L 650,583 L 1136,583 L 1136,437 L 1180,437')"/>`
          ).join('')}
        </g>
        <!-- Refoulement : sondes → retour bassin -->
        <g class="flow-ret">
          ${[1,2,3,4,5,6].map(i =>
            `<circle class="water-particle p${i}" r="3"
             style="offset-path: path('M 1180,437 L 1180,706 L 28,706 L 28,653')"/>`
          ).join('')}
        </g>

        <!-- ───────── NUMÉROS (badges sur les éléments) ───────── -->
        <g font-family="'Inter', system-ui, sans-serif" font-size="13" font-weight="700">
          <circle cx="258" cy="556" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="258" y="561" text-anchor="middle" fill="#fff">1</text>
          <circle cx="80" cy="864" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="80" y="869" text-anchor="middle" fill="#fff">2</text>
          <circle cx="450" cy="640" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="450" y="645" text-anchor="middle" fill="#fff">3</text>
          <circle cx="380" cy="450" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="380" y="455" text-anchor="middle" fill="#fff">4</text>
          <circle cx="1310" cy="490" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="1310" y="495" text-anchor="middle" fill="#fff">5</text>
          <circle cx="900" cy="468" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="900" y="473" text-anchor="middle" fill="#fff">6</text>
          <circle cx="1040" cy="468" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="1040" y="473" text-anchor="middle" fill="#fff">7</text>
          <circle cx="34" cy="640" r="14" fill="#1d4ed8" stroke="#fff" stroke-width="2"/>
          <text x="34" y="645" text-anchor="middle" fill="#fff">8</text>
        </g>

        <!-- ───────── ENCART LÉGENDE EN HAUT-GAUCHE ───────── -->
        <g font-family="'Inter', system-ui, sans-serif">
          <rect x="20" y="20" width="320" height="290" rx="10"
                fill="#0b1620" stroke="#1e293b" stroke-width="1" opacity="0.94"/>
          <text x="36" y="50" font-size="14" font-weight="700" fill="#f8fafc" letter-spacing="0.08em">CIRCUIT HYDRAULIQUE</text>
          <text x="36" y="68" font-size="10" font-weight="500" fill="#4cc9f0" letter-spacing="0.18em">ORDRE DES ÉLÉMENTS</text>

          <g font-size="11.5" fill="#e2e8f0">
            <circle cx="50" cy="96" r="10" fill="#1d4ed8"/><text x="50" y="100" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">1</text>
            <text x="68" y="100">Aspiration via skimmer</text>

            <circle cx="50" cy="124" r="10" fill="#1d4ed8"/><text x="50" y="128" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">2</text>
            <text x="68" y="128">Aspiration via bonde de fond</text>

            <circle cx="50" cy="152" r="10" fill="#1d4ed8"/><text x="50" y="156" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">3</text>
            <text x="68" y="156">Pompe de filtration</text>

            <circle cx="50" cy="180" r="10" fill="#1d4ed8"/><text x="50" y="184" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">4</text>
            <text x="68" y="184">Filtre à sable</text>

            <circle cx="50" cy="208" r="10" fill="#1d4ed8"/><text x="50" y="212" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">5</text>
            <text x="68" y="212">Pompe à chaleur (via by-pass)</text>

            <circle cx="50" cy="236" r="10" fill="#1d4ed8"/><text x="50" y="240" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">6</text>
            <text x="68" y="240">Analyse et injection pH</text>

            <circle cx="50" cy="264" r="10" fill="#1d4ed8"/><text x="50" y="268" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">7</text>
            <text x="68" y="268">Analyse et injection chlore</text>

            <circle cx="50" cy="292" r="10" fill="#1d4ed8"/><text x="50" y="296" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">8</text>
            <text x="68" y="296">Retour piscine</text>
          </g>
        </g>

        <!-- Badge "Sens de circulation de l'eau" -->
        <g font-family="'Inter', system-ui, sans-serif">
          <rect x="20" y="900" width="240" height="42" rx="8" fill="#0b1620" opacity="0.92"/>
          <path d="M 38,921 L 60,921 M 54,915 L 60,921 L 54,927" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <text x="76" y="926" font-size="12" fill="#e2e8f0">Sens de circulation de l'eau</text>
        </g>

        <!-- ───────── FRISE PÉDAGOGIQUE EN BAS ───────── -->
        <g font-family="'Inter', system-ui, sans-serif">
          <rect x="290" y="800" width="1100" height="140" rx="10"
                fill="#f8fafc" stroke="#cbd5e1" stroke-width="1" opacity="0.96"/>
          ${[
            {n:1, label:'Aspiration', sub:'skimmer'},
            {n:2, label:'Aspiration', sub:'bonde de fond'},
            {n:3, label:'Pompe de', sub:'filtration'},
            {n:4, label:'Filtre à', sub:'sable'},
            {n:5, label:'Pompe à chaleur', sub:'(via by-pass)'},
            {n:6, label:'Analyse et', sub:'injection pH'},
            {n:7, label:'Analyse et', sub:'injection chlore'},
            {n:8, label:'Retour', sub:'piscine'},
          ].map((step, idx) => {
            const w = 124, gap = 6;
            const x = 300 + idx * (w + gap);
            const arrow = idx < 7
              ? `<path d="M ${x+w+1},870 L ${x+w+gap-1},870 M ${x+w+gap-5},866 L ${x+w+gap-1},870 L ${x+w+gap-5},874" stroke="#1d4ed8" stroke-width="2" fill="none" stroke-linecap="round"/>`
              : '';
            return `
              <circle cx="${x+w/2}" cy="822" r="13" fill="#1d4ed8" stroke="#fff" stroke-width="1.5"/>
              <text x="${x+w/2}" y="827" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">${step.n}</text>
              <text x="${x+w/2}" y="900" text-anchor="middle" font-size="11" font-weight="600" fill="#0f172a">${step.label}</text>
              <text x="${x+w/2}" y="916" text-anchor="middle" font-size="10" fill="#475569">${step.sub}</text>
              ${arrow}
            `;
          }).join('')}
        </g>

        <!-- Sigle BASSIN -->
        <text x="140" y="60" text-anchor="middle" font-family="Georgia,serif"
              font-size="11" fill="#f4a261" letter-spacing="0.18em">BASSIN</text>
        <text x="800" y="60" text-anchor="middle" font-family="Georgia,serif"
              font-size="10" fill="#7a7058" letter-spacing="0.18em">LOCAL TECHNIQUE</text>
        <text x="1300" y="60" text-anchor="middle" font-family="Georgia,serif"
              font-size="10" fill="#7a7058" letter-spacing="0.18em">EXTÉRIEUR</text>
      </svg>
    `;
  }
}

customElements.define('pool-control-panel', PoolControlPanel);
