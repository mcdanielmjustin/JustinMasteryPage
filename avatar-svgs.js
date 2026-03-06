/**
 * avatar-svgs.js
 * Defines window.__AVATAR_SVGS — 8 demographically distinct patient avatar SVGs.
 *
 * All avatars share:
 *   - viewBox="0 0 200 320"
 *   - Face anchor: head center cy=107, mouth baseline y=126
 *   - avatar-body transform-origin: 100px 185px
 *   - avatar-head transform-origin: 100px 130px
 *   - avatar-jaw  transform-origin: 100px 126px
 *   - Required IDs for CSS animations (see PLAN_avatar_overhaul.md §4)
 *   - Jaw path y=120–142, mouth at y=126 — compatible with shared MOUTH_PATHS
 *
 * Keys: young_male, young_female, adolescent_male, adolescent_female,
 *       adult_male, adult_female, elder_male, elder_female
 */
(function () {
  'use strict';

  /* ── Shared chair block (identical across all 8 avatars) ───────── */
  const CHAIR = `<g id="chair">
    <rect x="60" y="170" width="80" height="110" rx="6"
          fill="url(#g-chair)" stroke="#222" stroke-width="1.2"/>
    <rect x="52" y="255" width="96" height="18" rx="5"
          fill="#3a3a4a" stroke="#222" stroke-width="1"/>
    <rect x="46" y="230" width="16" height="44" rx="4"
          fill="#3a3a4a" stroke="#222" stroke-width="1"/>
    <rect x="138" y="230" width="16" height="44" rx="4"
          fill="#3a3a4a" stroke="#222" stroke-width="1"/>
    <rect x="56" y="273" width="8"  height="36" rx="3" fill="#2a2a38"/>
    <rect x="136" y="273" width="8" height="36" rx="3" fill="#2a2a38"/>
    <rect x="66" y="278" width="6"  height="30" rx="2" fill="#252530"/>
    <rect x="128" y="278" width="6" height="30" rx="2" fill="#252530"/>
    <rect x="56" y="292" width="88" height="5"  rx="2" fill="#2a2a38"/>
    <ellipse cx="100" cy="312" rx="44" ry="5" fill="rgba(0,0,0,0.25)"/>
  </g>`;

  /* ── Shared defs: chair gradient + drop shadow filter ──────────── */
  const SHARED_DEFS = `
    <linearGradient id="g-chair" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#4a4a5a"/>
      <stop offset="100%" stop-color="#2e2e3a"/>
    </linearGradient>
    <filter id="f-avatar-shadow" x="-20%" y="-10%" width="140%" height="130%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="rgba(0,0,0,0.35)"/>
    </filter>`;

  /* ── SVG wrapper helper ─────────────────────────────────────────── */
  function wrap(defs, body) {
    return `<svg id="avatar-root" viewBox="0 0 200 320"
     xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:100%;overflow:visible">
  <defs>${defs}${SHARED_DEFS}
  </defs>
  ${CHAIR}
  ${body}
</svg>`;
  }

  /* ════════════════════════════════════════════════════════════════
     1. adult_male — baseline
     Head rx=29 ry=34, dark brown hair, blue shirt, medium skin
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS = {};

  window.__AVATAR_SVGS.adult_male = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f0b878"/>
      <stop offset="100%" stop-color="#e8a858"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f5c08e"/>
      <stop offset="100%" stop-color="#edaa68"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#5b6fa6"/>
      <stop offset="100%" stop-color="#3b4f7e"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <!-- Legs -->
    <g id="avatar-legs">
      <rect x="74" y="220" width="22" height="50" rx="8" fill="url(#g-cloth)"/>
      <rect x="104" y="220" width="22" height="50" rx="8" fill="url(#g-cloth)"/>
      <rect x="76" y="262" width="18" height="32" rx="6" fill="#374a7a"/>
      <rect x="106" y="262" width="18" height="32" rx="6" fill="#374a7a"/>
      <ellipse cx="85"  cy="295" rx="13" ry="7" fill="#282828"/>
      <ellipse cx="81"  cy="293" rx="5"  ry="3" fill="rgba(255,255,255,0.08)"/>
      <ellipse cx="115" cy="295" rx="13" ry="7" fill="#282828"/>
      <ellipse cx="111" cy="293" rx="5"  ry="3" fill="rgba(255,255,255,0.08)"/>
    </g>
    <!-- Torso -->
    <path d="M72 185 Q68 205 70 230 L130 230 Q132 205 128 185 Q114 175 100 175 Q86 175 72 185Z"
          fill="url(#g-cloth)"/>
    <path d="M93 183 L100 196 L107 183" fill="none"
          stroke="rgba(255,255,255,0.18)" stroke-width="1.5"
          stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="100" y1="196" x2="100" y2="226"
          stroke="rgba(0,0,0,0.15)" stroke-width="1"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M73 188 Q60 198 62 218 Q68 224 74 218 Q72 202 80 194Z" fill="url(#g-cloth)"/>
      <path d="M127 188 Q140 198 138 218 Q132 224 126 218 Q128 202 120 194Z" fill="url(#g-cloth)"/>
      <path d="M62 218 Q58 234 62 248 Q68 252 72 246 Q68 232 74 218Z" fill="url(#g-skin)"/>
      <path d="M138 218 Q142 234 138 248 Q132 252 128 246 Q132 232 126 218Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 214px">
        <path d="M76 248 Q72 256 76 264 Q84 268 92 264 Q96 258 94 250 Q86 246 76 248Z" fill="url(#g-skin)"/>
        <path d="M124 248 Q128 256 124 264 Q116 268 108 264 Q104 258 106 250 Q114 246 124 248Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="258" rx="10" ry="6" fill="url(#g-skin)" stroke="#dba070" stroke-width="0.5"/>
        <line x1="83"  y1="256" x2="82"  y2="263" stroke="#dba070" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="88"  y1="254" x2="87"  y2="262" stroke="#dba070" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="112" y1="256" x2="113" y2="263" stroke="#dba070" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="117" y1="254" x2="118" y2="262" stroke="#dba070" stroke-width="0.8" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <ellipse cx="100" cy="100" rx="34" ry="38" fill="#3a2010"/>
        <path d="M68 100 Q62 115 66 128" fill="none" stroke="#3a2010" stroke-width="8" stroke-linecap="round"/>
        <path d="M132 100 Q138 115 134 128" fill="none" stroke="#3a2010" stroke-width="8" stroke-linecap="round"/>
      </g>
      <rect x="91" y="134" width="18" height="22" rx="4" fill="url(#g-skin)"/>
      <line x1="91" y1="140" x2="109" y2="140" stroke="rgba(0,0,0,0.1)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="29" ry="34" fill="url(#g-skin-face)"/>
      <ellipse cx="71"  cy="110" rx="5" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="71"  cy="110" rx="2.5" ry="4" fill="#e8a87c"/>
      <ellipse cx="129" cy="110" rx="5" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="129" cy="110" rx="2.5" ry="4" fill="#e8a87c"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <path d="M82 93 Q88 90 94 92" fill="none" stroke="#5a3010" stroke-width="2.2" stroke-linecap="round"/>
          <path d="M106 92 Q112 90 118 93" fill="none" stroke="#5a3010" stroke-width="2.2" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="8" ry="7"   fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="112" cy="107" rx="8" ry="7"   fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="88"  cy="107" rx="7" ry="5.5" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="7" ry="5.5" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.8" fill="#5a7ab5"/>
          <circle  cx="112" cy="107" r="3.8" fill="#5a7ab5"/>
          <circle  cx="88"  cy="107" r="2"   fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="2"   fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="1" fill="rgba(255,255,255,0.75)"/>
          <circle  cx="113.5" cy="105.5" r="1" fill="rgba(255,255,255,0.75)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#c08060" stroke-width="0.8" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#c08060" stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c08060" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.1)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.1)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M75 120 Q78 136 100 142 Q122 136 125 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="6" ry="2.5" fill="rgba(255,255,255,0.12)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b07050" stroke-width="1.8" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c08860"
                stroke-width="0.9" stroke-linecap="round"/>
          <ellipse cx="96"  cy="133" rx="3" ry="1.2" fill="rgba(80,40,10,0.12)"/>
          <ellipse cx="104" cy="133" rx="3" ry="1.2" fill="rgba(80,40,10,0.12)"/>
          <ellipse cx="100" cy="135" rx="4" ry="1.2" fill="rgba(80,40,10,0.10)"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     2. adult_female
     Head rx=27 ry=33, shoulder-length dark hair, teal blouse, warm skin
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.adult_female = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f6c8a0"/>
      <stop offset="100%" stop-color="#eaaa78"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#fad4b0"/>
      <stop offset="100%" stop-color="#f0b888"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#5a8a7a"/>
      <stop offset="100%" stop-color="#3a6a5a"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <rect x="76"  y="220" width="20" height="48" rx="8" fill="#2e2e48"/>
      <rect x="104" y="220" width="20" height="48" rx="8" fill="#2e2e48"/>
      <rect x="78"  y="261" width="16" height="30" rx="6" fill="#242438"/>
      <rect x="106" y="261" width="16" height="30" rx="6" fill="#242438"/>
      <ellipse cx="86"  cy="292" rx="11" ry="6" fill="#282838"/>
      <ellipse cx="83"  cy="290" rx="4"  ry="2.5" fill="rgba(255,255,255,0.07)"/>
      <ellipse cx="114" cy="292" rx="11" ry="6" fill="#282838"/>
      <ellipse cx="111" cy="290" rx="4"  ry="2.5" fill="rgba(255,255,255,0.07)"/>
    </g>
    <!-- Torso — blouse -->
    <path d="M74 187 Q70 206 72 228 L128 228 Q130 206 126 187 Q113 178 100 178 Q87 178 74 187Z"
          fill="url(#g-cloth)"/>
    <path d="M94 185 L100 194 L106 185" fill="none"
          stroke="rgba(255,255,255,0.22)" stroke-width="1.4"
          stroke-linecap="round" stroke-linejoin="round"/>
    <g id="avatar-arms">
      <path d="M75 190 Q62 200 64 219 Q70 225 75 219 Q73 204 82 196Z" fill="url(#g-cloth)"/>
      <path d="M125 190 Q138 200 136 219 Q130 225 125 219 Q127 204 118 196Z" fill="url(#g-cloth)"/>
      <path d="M64 219 Q60 234 64 247 Q70 251 74 245 Q70 231 75 219Z" fill="url(#g-skin)"/>
      <path d="M136 219 Q140 234 136 247 Q130 251 126 245 Q130 231 125 219Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 214px">
        <path d="M76 247 Q72 255 76 263 Q84 267 91 263 Q95 257 93 249 Q86 245 76 247Z" fill="url(#g-skin)"/>
        <path d="M124 247 Q128 255 124 263 Q116 267 109 263 Q105 257 107 249 Q114 245 124 247Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="257" rx="9" ry="5.5" fill="url(#g-skin)" stroke="#dba880" stroke-width="0.5"/>
        <line x1="84"  y1="255" x2="83"  y2="262" stroke="#dba880" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="89"  y1="253" x2="88"  y2="260" stroke="#dba880" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="111" y1="255" x2="112" y2="262" stroke="#dba880" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="116" y1="253" x2="117" y2="260" stroke="#dba880" stroke-width="0.7" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <ellipse cx="100" cy="99" rx="30" ry="40" fill="#3a1a08"/>
        <path d="M70 98 Q63 120 66 148 Q69 158 74 162" fill="none"
              stroke="#3a1a08" stroke-width="12" stroke-linecap="round"/>
        <path d="M130 98 Q137 120 134 148 Q131 158 126 162" fill="none"
              stroke="#3a1a08" stroke-width="12" stroke-linecap="round"/>
        <path d="M80 78 Q100 72 120 78" fill="none"
              stroke="#3a1a08" stroke-width="6" stroke-linecap="round"/>
      </g>
      <rect x="92" y="134" width="16" height="20" rx="4" fill="url(#g-skin)"/>
      <line x1="92" y1="140" x2="108" y2="140" stroke="rgba(0,0,0,0.1)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="27" ry="33" fill="url(#g-skin-face)"/>
      <ellipse cx="73"  cy="110" rx="4.5" ry="6.5" fill="url(#g-skin)"/>
      <ellipse cx="73"  cy="110" rx="2.2" ry="3.8" fill="#e8aa7c"/>
      <ellipse cx="127" cy="110" rx="4.5" ry="6.5" fill="url(#g-skin)"/>
      <ellipse cx="127" cy="110" rx="2.2" ry="3.8" fill="#e8aa7c"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <path d="M83 92 Q88 89 94 91" fill="none" stroke="#5a2808" stroke-width="1.8" stroke-linecap="round"/>
          <path d="M106 91 Q112 89 117 92" fill="none" stroke="#5a2808" stroke-width="1.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="7.5" ry="6.5" fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="112" cy="107" rx="7.5" ry="6.5" fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="88"  cy="107" rx="6.5" ry="5.2" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="6.5" ry="5.2" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.6" fill="#7a9060"/>
          <circle  cx="112" cy="107" r="3.6" fill="#7a9060"/>
          <circle  cx="88"  cy="107" r="1.9" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="1.9" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="1" fill="rgba(255,255,255,0.78)"/>
          <circle  cx="113.5" cy="105.5" r="1" fill="rgba(255,255,255,0.78)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#c08870" stroke-width="0.7" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#c08870" stroke-width="0.7" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c08870" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M76 120 Q79 136 100 142 Q121 136 124 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="5.5" ry="2.2" fill="rgba(255,255,255,0.13)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b07870" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c09070"
                stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     3. young_male
     Head rx=32 ry=37, messy dark hair, blue T-shirt, medium olive skin
     Shorter body; feet barely reach chair
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.young_male = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f7c98a"/>
      <stop offset="100%" stop-color="#e8a860"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#fad6a0"/>
      <stop offset="100%" stop-color="#f0b870"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#4a7ab8"/>
      <stop offset="100%" stop-color="#2a5a98"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <rect x="76"  y="222" width="20" height="42" rx="8" fill="url(#g-cloth)"/>
      <rect x="104" y="222" width="20" height="42" rx="8" fill="url(#g-cloth)"/>
      <rect x="78"  y="257" width="16" height="26" rx="6" fill="#3a5a8a"/>
      <rect x="106" y="257" width="16" height="26" rx="6" fill="#3a5a8a"/>
      <ellipse cx="86"  cy="285" rx="11" ry="6" fill="#282828"/>
      <ellipse cx="82"  cy="283" rx="4"  ry="2.5" fill="rgba(255,255,255,0.08)"/>
      <ellipse cx="114" cy="285" rx="11" ry="6" fill="#282828"/>
      <ellipse cx="110" cy="283" rx="4"  ry="2.5" fill="rgba(255,255,255,0.08)"/>
    </g>
    <!-- Torso — T-shirt, shorter -->
    <path d="M76 192 Q72 208 74 222 L126 222 Q128 208 124 192 Q112 183 100 183 Q88 183 76 192Z"
          fill="url(#g-cloth)"/>
    <!-- Crew neck -->
    <path d="M90 188 Q100 192 110 188" fill="none"
          stroke="rgba(255,255,255,0.20)" stroke-width="1.5"
          stroke-linecap="round"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M77 195 Q64 204 66 220 Q72 225 77 220 Q75 208 84 199Z" fill="url(#g-cloth)"/>
      <path d="M123 195 Q136 204 134 220 Q128 225 123 220 Q125 208 116 199Z" fill="url(#g-cloth)"/>
      <path d="M66 220 Q62 232 66 244 Q71 248 75 242 Q71 230 77 220Z" fill="url(#g-skin)"/>
      <path d="M134 220 Q138 232 134 244 Q129 248 125 242 Q129 230 123 220Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 208px">
        <path d="M77 244 Q73 251 77 258 Q84 262 91 258 Q95 252 93 245 Q86 241 77 244Z" fill="url(#g-skin)"/>
        <path d="M123 244 Q127 251 123 258 Q116 262 109 258 Q105 252 107 245 Q114 241 123 244Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="252" rx="9" ry="5" fill="url(#g-skin)" stroke="#e0a060" stroke-width="0.5"/>
        <line x1="84"  y1="250" x2="83"  y2="257" stroke="#e0a060" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="89"  y1="248" x2="88"  y2="256" stroke="#e0a060" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="111" y1="250" x2="112" y2="257" stroke="#e0a060" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="116" y1="248" x2="117" y2="256" stroke="#e0a060" stroke-width="0.8" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head — larger (child proportions) -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <ellipse cx="100" cy="98" rx="35" ry="36" fill="#2a1a08"/>
        <!-- Messy bumps on top -->
        <ellipse cx="90"  cy="77" rx="8" ry="6" fill="#2a1a08"/>
        <ellipse cx="100" cy="74" rx="9" ry="7" fill="#2a1a08"/>
        <ellipse cx="111" cy="77" rx="8" ry="6" fill="#2a1a08"/>
        <path d="M66 100 Q60 112 63 122" fill="none" stroke="#2a1a08" stroke-width="7" stroke-linecap="round"/>
        <path d="M134 100 Q140 112 137 122" fill="none" stroke="#2a1a08" stroke-width="7" stroke-linecap="round"/>
      </g>
      <rect x="92" y="138" width="16" height="16" rx="4" fill="url(#g-skin)"/>
      <line x1="92" y1="143" x2="108" y2="143" stroke="rgba(0,0,0,0.08)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="32" ry="37" fill="url(#g-skin-face)"/>
      <ellipse cx="68"  cy="110" rx="5.5" ry="7.5" fill="url(#g-skin)"/>
      <ellipse cx="68"  cy="110" rx="2.6" ry="4.2" fill="#e0a060"/>
      <ellipse cx="132" cy="110" rx="5.5" ry="7.5" fill="url(#g-skin)"/>
      <ellipse cx="132" cy="110" rx="2.6" ry="4.2" fill="#e0a060"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <path d="M82 93 Q88 90 94 92" fill="none" stroke="#5a3818" stroke-width="1.6" stroke-linecap="round"/>
          <path d="M106 92 Q112 90 118 93" fill="none" stroke="#5a3818" stroke-width="1.6" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <!-- Larger eyes — child proportion -->
          <ellipse cx="88"  cy="107" rx="8.5" ry="7.5" fill="rgba(0,0,0,0.05)"/>
          <ellipse cx="112" cy="107" rx="8.5" ry="7.5" fill="rgba(0,0,0,0.05)"/>
          <ellipse cx="88"  cy="107" rx="7.5" ry="6.5" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="7.5" ry="6.5" fill="#fff"/>
          <circle  cx="88"  cy="107" r="4.2" fill="#5a8a70"/>
          <circle  cx="112" cy="107" r="4.2" fill="#5a8a70"/>
          <circle  cx="88"  cy="107" r="2.2" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="2.2" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.2" r="1.2" fill="rgba(255,255,255,0.80)"/>
          <circle  cx="113.5" cy="105.2" r="1.2" fill="rgba(255,255,255,0.80)"/>
          <path d="M81 104 Q88 100 95 104" fill="none" stroke="#c09060" stroke-width="0.7" stroke-linecap="round"/>
          <path d="M105 104 Q112 100 119 104" fill="none" stroke="#c09060" stroke-width="0.7" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c09060" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.2" ry="1.3" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.2" ry="1.3" fill="rgba(0,0,0,0.08)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <!-- Jaw fits wider head (x=71/129) -->
          <path d="M71 120 Q74 136 100 142 Q126 136 129 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="6" ry="2.5" fill="rgba(255,255,255,0.11)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#c08858" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c09060"
                stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     4. young_female
     Head rx=31 ry=36, pigtails (auburn), rose/pink top, purple leggings
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.young_female = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f9d4a0"/>
      <stop offset="100%" stop-color="#f0b878"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#fde0b4"/>
      <stop offset="100%" stop-color="#f4c28a"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#c06888"/>
      <stop offset="100%" stop-color="#a04868"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <!-- Leggings -->
      <rect x="78"  y="222" width="19" height="40" rx="8" fill="#5a4090"/>
      <rect x="103" y="222" width="19" height="40" rx="8" fill="#5a4090"/>
      <rect x="80"  y="255" width="15" height="25" rx="6" fill="#3a2870"/>
      <rect x="105" y="255" width="15" height="25" rx="6" fill="#3a2870"/>
      <!-- Mary-Jane shoes -->
      <ellipse cx="87"  cy="281" rx="11" ry="5.5" fill="#1a1428"/>
      <ellipse cx="113" cy="281" rx="11" ry="5.5" fill="#1a1428"/>
      <rect x="82" y="276" width="10" height="2.5" rx="1.2" fill="#1a1428"/>
      <rect x="108" y="276" width="10" height="2.5" rx="1.2" fill="#1a1428"/>
      <ellipse cx="84"  cy="279" rx="3" ry="1.5" fill="rgba(255,255,255,0.07)"/>
      <ellipse cx="110" cy="279" rx="3" ry="1.5" fill="rgba(255,255,255,0.07)"/>
    </g>
    <!-- Torso — rose top, narrower -->
    <path d="M78 193 Q74 208 76 222 L124 222 Q126 208 122 193 Q111 184 100 184 Q89 184 78 193Z"
          fill="url(#g-cloth)"/>
    <path d="M91 189 Q100 193 109 189" fill="none"
          stroke="rgba(255,255,255,0.20)" stroke-width="1.5" stroke-linecap="round"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M79 196 Q66 205 68 220 Q73 225 79 220 Q77 209 85 200Z" fill="url(#g-cloth)"/>
      <path d="M121 196 Q134 205 132 220 Q127 225 121 220 Q123 209 115 200Z" fill="url(#g-cloth)"/>
      <path d="M68 220 Q64 232 68 244 Q73 248 77 242 Q73 230 79 220Z" fill="url(#g-skin)"/>
      <path d="M132 220 Q136 232 132 244 Q127 248 123 242 Q127 230 121 220Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 208px">
        <path d="M78 244 Q74 251 78 258 Q85 262 91 258 Q95 252 93 245 Q86 241 78 244Z" fill="url(#g-skin)"/>
        <path d="M122 244 Q126 251 122 258 Q115 262 109 258 Q105 252 107 245 Q114 241 122 244Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="252" rx="9" ry="5" fill="url(#g-skin)" stroke="#e8b080" stroke-width="0.5"/>
        <line x1="84"  y1="250" x2="83"  y2="257" stroke="#e8b080" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="89"  y1="248" x2="88"  y2="256" stroke="#e8b080" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="111" y1="250" x2="112" y2="257" stroke="#e8b080" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="116" y1="248" x2="117" y2="256" stroke="#e8b080" stroke-width="0.7" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <!-- Back mass -->
        <ellipse cx="100" cy="100" rx="33" ry="38" fill="#7a3818"/>
        <!-- Left pigtail bundle -->
        <ellipse cx="62"  cy="108" rx="10" ry="14" fill="#7a3818"/>
        <path d="M65 120 Q60 140 64 155" fill="none"
              stroke="#7a3818" stroke-width="9" stroke-linecap="round"/>
        <!-- Right pigtail bundle -->
        <ellipse cx="138" cy="108" rx="10" ry="14" fill="#7a3818"/>
        <path d="M135 120 Q140 140 136 155" fill="none"
              stroke="#7a3818" stroke-width="9" stroke-linecap="round"/>
        <!-- Hair ties -->
        <circle cx="64"  cy="124" r="4.5" fill="#e04060"/>
        <circle cx="136" cy="124" r="4.5" fill="#e04060"/>
        <!-- Center part -->
        <path d="M100 73 L100 89" stroke="#5a2010" stroke-width="2" stroke-linecap="round"/>
      </g>
      <rect x="93" y="137" width="14" height="18" rx="4" fill="url(#g-skin)"/>
      <line x1="93" y1="142" x2="107" y2="142" stroke="rgba(0,0,0,0.08)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="31" ry="36" fill="url(#g-skin-face)"/>
      <ellipse cx="69"  cy="110" rx="5.2" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="69"  cy="110" rx="2.4" ry="4" fill="#e8b080"/>
      <ellipse cx="131" cy="110" rx="5.2" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="131" cy="110" rx="2.4" ry="4" fill="#e8b080"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <path d="M83 92 Q88 89 94 91" fill="none" stroke="#7a3818" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M106 91 Q112 89 117 92" fill="none" stroke="#7a3818" stroke-width="1.5" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="8.2" ry="7.2" fill="rgba(0,0,0,0.05)"/>
          <ellipse cx="112" cy="107" rx="8.2" ry="7.2" fill="rgba(0,0,0,0.05)"/>
          <ellipse cx="88"  cy="107" rx="7.2" ry="6.2" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="7.2" ry="6.2" fill="#fff"/>
          <circle  cx="88"  cy="107" r="4.0" fill="#5a9a60"/>
          <circle  cx="112" cy="107" r="4.0" fill="#5a9a60"/>
          <circle  cx="88"  cy="107" r="2.1" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="2.1" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.2" r="1.2" fill="rgba(255,255,255,0.82)"/>
          <circle  cx="113.5" cy="105.2" r="1.2" fill="rgba(255,255,255,0.82)"/>
          <path d="M81 103 Q88 100 95 103" fill="none" stroke="#c09870" stroke-width="0.7" stroke-linecap="round"/>
          <path d="M105 103 Q112 100 119 103" fill="none" stroke="#c09870" stroke-width="0.7" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c09870" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.2" ry="1.3" fill="rgba(0,0,0,0.07)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.2" ry="1.3" fill="rgba(0,0,0,0.07)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M71 120 Q74 136 100 143 Q126 136 129 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="140" rx="5.5" ry="2.2" fill="rgba(255,255,255,0.13)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#c08878" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c09878"
                stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     5. adolescent_male
     Head rx=30 ry=35, dark undercut hair, hoodie, medium tan skin
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.adolescent_male = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f2b870"/>
      <stop offset="100%" stop-color="#d89848"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f6c888"/>
      <stop offset="100%" stop-color="#e0a858"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#5a6a9a"/>
      <stop offset="100%" stop-color="#3a4a7a"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <rect x="74"  y="222" width="22" height="48" rx="8" fill="#2a3858"/>
      <rect x="104" y="222" width="22" height="48" rx="8" fill="#2a3858"/>
      <rect x="76"  y="263" width="18" height="30" rx="6" fill="#1a2840"/>
      <rect x="106" y="263" width="18" height="30" rx="6" fill="#1a2840"/>
      <!-- Chunky sneakers -->
      <rect x="72" y="290" width="28" height="10" rx="4" fill="#303040"/>
      <rect x="100" y="290" width="28" height="10" rx="4" fill="#303040"/>
      <rect x="71" y="296" width="30" height="5"  rx="3" fill="#1a1a28"/>
      <rect x="99" y="296" width="30" height="5"  rx="3" fill="#1a1a28"/>
      <ellipse cx="84"  cy="292" rx="6" ry="2" fill="rgba(255,255,255,0.07)"/>
      <ellipse cx="114" cy="292" rx="6" ry="2" fill="rgba(255,255,255,0.07)"/>
    </g>
    <!-- Torso — hoodie -->
    <path d="M74 188 Q70 207 72 228 L128 228 Q130 207 126 188 Q114 178 100 178 Q86 178 74 188Z"
          fill="url(#g-cloth)"/>
    <!-- Hoodie kangaroo pocket -->
    <path d="M82 210 Q100 215 118 210" fill="none"
          stroke="rgba(255,255,255,0.08)" stroke-width="1.2" stroke-linecap="round"/>
    <!-- Hood seam -->
    <path d="M88 183 Q100 188 112 183" fill="none"
          stroke="rgba(255,255,255,0.12)" stroke-width="1.2" stroke-linecap="round"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M75 191 Q62 201 64 219 Q70 225 75 219 Q73 205 82 197Z" fill="url(#g-cloth)"/>
      <path d="M125 191 Q138 201 136 219 Q130 225 125 219 Q127 205 118 197Z" fill="url(#g-cloth)"/>
      <path d="M64 219 Q60 234 64 247 Q70 251 74 245 Q70 231 75 219Z" fill="url(#g-skin)"/>
      <path d="M136 219 Q140 234 136 247 Q130 251 126 245 Q130 231 125 219Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 213px">
        <path d="M76 247 Q72 255 76 263 Q84 267 91 263 Q95 257 93 248 Q86 244 76 247Z" fill="url(#g-skin)"/>
        <path d="M124 247 Q128 255 124 263 Q116 267 109 263 Q105 257 107 248 Q114 244 124 247Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="257" rx="9.5" ry="5.5" fill="url(#g-skin)" stroke="#d89848" stroke-width="0.5"/>
        <line x1="83"  y1="255" x2="82"  y2="262" stroke="#d89848" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="88"  y1="253" x2="87"  y2="261" stroke="#d89848" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="112" y1="255" x2="113" y2="262" stroke="#d89848" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="117" y1="253" x2="118" y2="261" stroke="#d89848" stroke-width="0.8" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <!-- Close-cropped sides -->
        <ellipse cx="100" cy="104" rx="33" ry="36" fill="#181008"/>
        <!-- Longer swept top -->
        <ellipse cx="102" cy="86" rx="26" ry="18" fill="#181008"/>
        <!-- Top fringe swept left-to-right -->
        <path d="M76 86 Q90 76 116 82 Q121 84 119 88" fill="#181008" stroke="none"/>
        <!-- Side taper lines -->
        <path d="M68 102 Q63 114 65 125" fill="none" stroke="#181008" stroke-width="7" stroke-linecap="round"/>
        <path d="M132 102 Q137 114 135 125" fill="none" stroke="#181008" stroke-width="7" stroke-linecap="round"/>
      </g>
      <rect x="91" y="135" width="18" height="21" rx="4" fill="url(#g-skin)"/>
      <line x1="91" y1="141" x2="109" y2="141" stroke="rgba(0,0,0,0.1)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="30" ry="35" fill="url(#g-skin-face)"/>
      <ellipse cx="70"  cy="110" rx="5" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="70"  cy="110" rx="2.4" ry="4" fill="#d89848"/>
      <ellipse cx="130" cy="110" rx="5" ry="7" fill="url(#g-skin)"/>
      <ellipse cx="130" cy="110" rx="2.4" ry="4" fill="#d89848"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <!-- Thicker teen brows -->
          <path d="M82 93 Q88 90 94 92" fill="none" stroke="#281808" stroke-width="2.4" stroke-linecap="round"/>
          <path d="M106 92 Q112 90 118 93" fill="none" stroke="#281808" stroke-width="2.4" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="8"   ry="7"   fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="112" cy="107" rx="8"   ry="7"   fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="88"  cy="107" rx="7"   ry="5.8" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="7"   ry="5.8" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.9"  fill="#6a7a90"/>
          <circle  cx="112" cy="107" r="3.9"  fill="#6a7a90"/>
          <circle  cx="88"  cy="107" r="2.1"  fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="2.1"  fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="1" fill="rgba(255,255,255,0.75)"/>
          <circle  cx="113.5" cy="105.5" r="1" fill="rgba(255,255,255,0.75)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#b08040" stroke-width="0.8" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#b08040" stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#b08040" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.09)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.09)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <!-- Slightly angular adolescent jaw -->
          <path d="M72 120 Q75 137 100 143 Q125 137 128 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="140" rx="6" ry="2.5" fill="rgba(255,255,255,0.11)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b07840" stroke-width="1.8" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c08850"
                stroke-width="0.9" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     6. adolescent_female
     Head rx=28 ry=34, shoulder-length brown hair, purple top, warm skin
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.adolescent_female = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f8c890"/>
      <stop offset="100%" stop-color="#eaaa68"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#fcd4a4"/>
      <stop offset="100%" stop-color="#f0b878"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#9a60b0"/>
      <stop offset="100%" stop-color="#7a4090"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <!-- Dark leggings -->
      <rect x="77"  y="220" width="21" height="46" rx="8" fill="#2e2040"/>
      <rect x="102" y="220" width="21" height="46" rx="8" fill="#2e2040"/>
      <rect x="79"  y="259" width="17" height="28" rx="6" fill="#1e1030"/>
      <rect x="104" y="259" width="17" height="28" rx="6" fill="#1e1030"/>
      <ellipse cx="88"  cy="289" rx="12" ry="6" fill="#1a1428"/>
      <ellipse cx="84"  cy="287" rx="4"  ry="2.5" fill="rgba(255,255,255,0.07)"/>
      <ellipse cx="112" cy="289" rx="12" ry="6" fill="#1a1428"/>
      <ellipse cx="108" cy="287" rx="4"  ry="2.5" fill="rgba(255,255,255,0.07)"/>
    </g>
    <!-- Torso — purple casual top -->
    <path d="M76 190 Q72 208 74 226 L126 226 Q128 208 124 190 Q112 181 100 181 Q88 181 76 190Z"
          fill="url(#g-cloth)"/>
    <path d="M94 187 L100 196 L106 187" fill="none"
          stroke="rgba(255,255,255,0.20)" stroke-width="1.4"
          stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M77 193 Q64 203 66 220 Q72 226 77 220 Q75 207 83 199Z" fill="url(#g-cloth)"/>
      <path d="M123 193 Q136 203 134 220 Q128 226 123 220 Q125 207 117 199Z" fill="url(#g-cloth)"/>
      <path d="M66 220 Q62 234 66 246 Q71 250 75 244 Q71 231 77 220Z" fill="url(#g-skin)"/>
      <path d="M134 220 Q138 234 134 246 Q129 250 125 244 Q129 231 123 220Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 212px">
        <path d="M77 246 Q73 253 77 260 Q84 264 91 260 Q95 254 93 247 Q86 242 77 246Z" fill="url(#g-skin)"/>
        <path d="M123 246 Q127 253 123 260 Q116 264 109 260 Q105 254 107 247 Q114 242 123 246Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="254" rx="9" ry="5" fill="url(#g-skin)" stroke="#e8aa70" stroke-width="0.5"/>
        <line x1="84"  y1="252" x2="83"  y2="259" stroke="#e8aa70" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="89"  y1="250" x2="88"  y2="258" stroke="#e8aa70" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="111" y1="252" x2="112" y2="259" stroke="#e8aa70" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="116" y1="250" x2="117" y2="258" stroke="#e8aa70" stroke-width="0.7" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <ellipse cx="100" cy="99" rx="30" ry="38" fill="#5a2808"/>
        <!-- Center part -->
        <path d="M100 72 L100 88" stroke="#3a1808" stroke-width="1.5" stroke-linecap="round"/>
        <!-- Left side falls -->
        <path d="M70 98 Q63 120 66 148 Q69 158 74 163" fill="none"
              stroke="#5a2808" stroke-width="11" stroke-linecap="round"/>
        <!-- Right side falls -->
        <path d="M130 98 Q137 120 134 148 Q131 158 126 163" fill="none"
              stroke="#5a2808" stroke-width="11" stroke-linecap="round"/>
        <!-- Slight curl at ends -->
        <path d="M73 161 Q70 167 76 169" fill="none"
              stroke="#5a2808" stroke-width="8" stroke-linecap="round"/>
        <path d="M127 161 Q130 167 124 169" fill="none"
              stroke="#5a2808" stroke-width="8" stroke-linecap="round"/>
      </g>
      <rect x="92" y="134" width="16" height="20" rx="4" fill="url(#g-skin)"/>
      <line x1="92" y1="140" x2="108" y2="140" stroke="rgba(0,0,0,0.09)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="28" ry="34" fill="url(#g-skin-face)"/>
      <ellipse cx="72"  cy="110" rx="4.8" ry="6.8" fill="url(#g-skin)"/>
      <ellipse cx="72"  cy="110" rx="2.3" ry="3.9" fill="#eaaa70"/>
      <ellipse cx="128" cy="110" rx="4.8" ry="6.8" fill="url(#g-skin)"/>
      <ellipse cx="128" cy="110" rx="2.3" ry="3.9" fill="#eaaa70"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <path d="M83 92 Q88 89 94 91" fill="none" stroke="#5a2808" stroke-width="1.8" stroke-linecap="round"/>
          <path d="M106 91 Q112 89 117 92" fill="none" stroke="#5a2808" stroke-width="1.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="7.8" ry="6.8" fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="112" cy="107" rx="7.8" ry="6.8" fill="rgba(0,0,0,0.06)"/>
          <ellipse cx="88"  cy="107" rx="6.8" ry="5.5" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="6.8" ry="5.5" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.7" fill="#8a6098"/>
          <circle  cx="112" cy="107" r="3.7" fill="#8a6098"/>
          <circle  cx="88"  cy="107" r="2.0" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="2.0" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="1" fill="rgba(255,255,255,0.78)"/>
          <circle  cx="113.5" cy="105.5" r="1" fill="rgba(255,255,255,0.78)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#c09070" stroke-width="0.7" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#c09070" stroke-width="0.7" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c09070" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
        </g>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M74 120 Q77 136 100 142 Q123 136 126 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="5.5" ry="2.2" fill="rgba(255,255,255,0.12)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b07860" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c08878"
                stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     7. elder_male
     Head rx=29 ry=33, sparse grey hair, wrinkles, brown cardigan
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.elder_male = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#e8b882"/>
      <stop offset="100%" stop-color="#d09a60"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#ecca94"/>
      <stop offset="100%" stop-color="#d8a870"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#7a6050"/>
      <stop offset="100%" stop-color="#5a4030"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <rect x="74"  y="220" width="22" height="46" rx="8" fill="#3a3028"/>
      <rect x="104" y="220" width="22" height="46" rx="8" fill="#3a3028"/>
      <rect x="76"  y="259" width="18" height="30" rx="6" fill="#2a2018"/>
      <rect x="106" y="259" width="18" height="30" rx="6" fill="#2a2018"/>
      <!-- Wider heavier shoes -->
      <ellipse cx="85"  cy="292" rx="14" ry="7" fill="#282018"/>
      <ellipse cx="80"  cy="290" rx="5"  ry="3" fill="rgba(255,255,255,0.06)"/>
      <ellipse cx="115" cy="292" rx="14" ry="7" fill="#282018"/>
      <ellipse cx="110" cy="290" rx="5"  ry="3" fill="rgba(255,255,255,0.06)"/>
    </g>
    <!-- Torso — cardigan with buttons -->
    <path d="M73 187 Q68 207 70 228 L130 228 Q132 207 127 187 Q114 177 100 177 Q86 177 73 187Z"
          fill="url(#g-cloth)"/>
    <!-- Lapels -->
    <path d="M93 184 L100 197 L107 184" fill="none"
          stroke="rgba(255,255,255,0.15)" stroke-width="1.5"
          stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Button row -->
    <line x1="100" y1="197" x2="100" y2="225"
          stroke="rgba(0,0,0,0.18)" stroke-width="1" stroke-dasharray="3,4"/>
    <circle cx="100" cy="202" r="2.2" fill="rgba(0,0,0,0.28)"/>
    <circle cx="100" cy="211" r="2.2" fill="rgba(0,0,0,0.28)"/>
    <circle cx="100" cy="220" r="2.2" fill="rgba(0,0,0,0.28)"/>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M74 190 Q61 200 63 219 Q69 225 74 219 Q72 204 81 196Z" fill="url(#g-cloth)"/>
      <path d="M126 190 Q139 200 137 219 Q131 225 126 219 Q128 204 119 196Z" fill="url(#g-cloth)"/>
      <path d="M63 219 Q59 234 63 248 Q69 252 73 246 Q69 232 74 219Z" fill="url(#g-skin)"/>
      <path d="M137 219 Q141 234 137 248 Q131 252 127 246 Q131 232 126 219Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 214px">
        <path d="M75 248 Q71 256 75 264 Q83 268 91 264 Q95 258 93 249 Q85 245 75 248Z" fill="url(#g-skin)"/>
        <path d="M125 248 Q129 256 125 264 Q117 268 109 264 Q105 258 107 249 Q115 245 125 248Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="258" rx="10" ry="6" fill="url(#g-skin)" stroke="#c89858" stroke-width="0.5"/>
        <line x1="83"  y1="256" x2="82"  y2="263" stroke="#c89858" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="88"  y1="254" x2="87"  y2="262" stroke="#c89858" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="112" y1="256" x2="113" y2="263" stroke="#c89858" stroke-width="0.8" stroke-linecap="round"/>
        <line x1="117" y1="254" x2="118" y2="262" stroke="#c89858" stroke-width="0.8" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <!-- Sparse white-grey wisps -->
        <path d="M76 86 Q87 80 100 79 Q113 80 124 86" fill="none"
              stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
        <path d="M80 83 Q90 78 100 77 Q110 78 120 83" fill="none"
              stroke="#c8c8d0" stroke-width="3" stroke-linecap="round"/>
        <path d="M68 97 Q62 110 64 124" fill="none"
              stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
        <path d="M132 97 Q138 110 136 124" fill="none"
              stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
        <!-- Thin halo of remaining hair -->
        <path d="M70 97 Q68 107 70 120 Q74 132 80 138" fill="none"
              stroke="#b8b8c0" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
        <path d="M130 97 Q132 107 130 120 Q126 132 120 138" fill="none"
              stroke="#b8b8c0" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
      </g>
      <rect x="91" y="133" width="18" height="21" rx="4" fill="url(#g-skin)"/>
      <line x1="91" y1="139" x2="109" y2="139" stroke="rgba(0,0,0,0.1)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="29" ry="33" fill="url(#g-skin-face)"/>
      <ellipse cx="71"  cy="110" rx="5"   ry="7"   fill="url(#g-skin)"/>
      <ellipse cx="71"  cy="110" rx="2.4" ry="4"   fill="#c89858"/>
      <ellipse cx="129" cy="110" rx="5"   ry="7"   fill="url(#g-skin)"/>
      <ellipse cx="129" cy="110" rx="2.4" ry="4"   fill="#c89858"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <!-- Lighter, bushier elder brows -->
          <path d="M82 93 Q88 90 94 92" fill="none" stroke="#a09080" stroke-width="2.6" stroke-linecap="round"/>
          <path d="M106 92 Q112 90 118 93" fill="none" stroke="#a09080" stroke-width="2.6" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <!-- Deeper set eye sockets -->
          <ellipse cx="88"  cy="107" rx="9" ry="8" fill="rgba(0,0,0,0.09)"/>
          <ellipse cx="112" cy="107" rx="9" ry="8" fill="rgba(0,0,0,0.09)"/>
          <ellipse cx="88"  cy="107" rx="7" ry="5.5" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="7" ry="5.5" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.5" fill="#7a8898"/>
          <circle  cx="112" cy="107" r="3.5" fill="#7a8898"/>
          <circle  cx="88"  cy="107" r="1.9" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="1.9" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="0.9" fill="rgba(255,255,255,0.65)"/>
          <circle  cx="113.5" cy="105.5" r="0.9" fill="rgba(255,255,255,0.65)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#c09870" stroke-width="0.8" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#c09870" stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c09870" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.1)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.5" ry="1.5" fill="rgba(0,0,0,0.1)"/>
        </g>
        <!-- Wrinkle lines -->
        <path d="M82 90 Q100 88 118 90" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="1" stroke-linecap="round"/>
        <path d="M84 85 Q100 83 116 85" fill="none" stroke="rgba(160,120,80,0.13)" stroke-width="0.8" stroke-linecap="round"/>
        <path d="M80 110 Q77 113 79 116" fill="none" stroke="rgba(160,120,80,0.20)" stroke-width="0.8" stroke-linecap="round"/>
        <path d="M80 111 Q76 115 78 118" fill="none" stroke="rgba(160,120,80,0.14)" stroke-width="0.7" stroke-linecap="round"/>
        <path d="M120 110 Q123 113 121 116" fill="none" stroke="rgba(160,120,80,0.20)" stroke-width="0.8" stroke-linecap="round"/>
        <path d="M120 111 Q124 115 122 118" fill="none" stroke="rgba(160,120,80,0.14)" stroke-width="0.7" stroke-linecap="round"/>
        <path d="M90 118 Q88 124 90 128" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.8" stroke-linecap="round"/>
        <path d="M110 118 Q112 124 110 128" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.8" stroke-linecap="round"/>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M75 120 Q78 136 100 142 Q122 136 125 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="6" ry="2.5" fill="rgba(255,255,255,0.10)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b08858" stroke-width="1.8" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c09868"
                stroke-width="0.9" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

  /* ════════════════════════════════════════════════════════════════
     8. elder_female
     Head rx=26 ry=32, white curly hair, wrinkles, mauve blouse, pearl necklace
  ════════════════════════════════════════════════════════════════ */
  window.__AVATAR_SVGS.elder_female = wrap(
    `<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f0c8a0"/>
      <stop offset="100%" stop-color="#e0aa80"/>
    </linearGradient>
    <linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#f6d4b0"/>
      <stop offset="100%" stop-color="#e8b888"/>
    </linearGradient>
    <linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#8a6070"/>
      <stop offset="100%" stop-color="#6a4050"/>
    </linearGradient>`,
    `<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
    <g id="avatar-legs">
      <rect x="78"  y="221" width="19" height="46" rx="8" fill="#38303a"/>
      <rect x="103" y="221" width="19" height="46" rx="8" fill="#38303a"/>
      <rect x="80"  y="260" width="15" height="28" rx="6" fill="#28202a"/>
      <rect x="105" y="260" width="15" height="28" rx="6" fill="#28202a"/>
      <ellipse cx="87"  cy="290" rx="12" ry="6"  fill="#2a2030"/>
      <ellipse cx="84"  cy="288" rx="4"  ry="2.5" fill="rgba(255,255,255,0.06)"/>
      <ellipse cx="113" cy="290" rx="12" ry="6"  fill="#2a2030"/>
      <ellipse cx="110" cy="288" rx="4"  ry="2.5" fill="rgba(255,255,255,0.06)"/>
    </g>
    <!-- Torso — mauve blouse -->
    <path d="M75 188 Q71 207 73 227 L127 227 Q129 207 125 188 Q113 179 100 179 Q87 179 75 188Z"
          fill="url(#g-cloth)"/>
    <!-- Blouse collar -->
    <path d="M94 185 L100 193 L106 185" fill="none"
          stroke="rgba(255,255,255,0.22)" stroke-width="1.4"
          stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Pearl necklace -->
    <g opacity="0.70">
      <circle cx="90"  cy="168" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
      <circle cx="95"  cy="165" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
      <circle cx="100" cy="164" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
      <circle cx="105" cy="165" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
      <circle cx="110" cy="168" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
    </g>
    <!-- Arms -->
    <g id="avatar-arms">
      <path d="M76 191 Q63 201 65 219 Q71 225 76 219 Q74 205 82 197Z" fill="url(#g-cloth)"/>
      <path d="M124 191 Q137 201 135 219 Q129 225 124 219 Q126 205 118 197Z" fill="url(#g-cloth)"/>
      <path d="M65 219 Q61 234 65 247 Q70 251 74 245 Q70 231 76 219Z" fill="url(#g-skin)"/>
      <path d="M135 219 Q139 234 135 247 Q130 251 126 245 Q130 231 124 219Z" fill="url(#g-skin)"/>
      <g id="avatar-hand" style="transform-origin:100px 213px">
        <path d="M75 247 Q71 255 75 263 Q83 267 90 263 Q94 257 92 248 Q85 244 75 247Z" fill="url(#g-skin)"/>
        <path d="M125 247 Q129 255 125 263 Q117 267 110 263 Q106 257 108 248 Q115 244 125 247Z" fill="url(#g-skin)"/>
        <ellipse cx="100" cy="257" rx="9.5" ry="5.5" fill="url(#g-skin)" stroke="#d8a878" stroke-width="0.5"/>
        <line x1="83"  y1="255" x2="82"  y2="262" stroke="#d8a878" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="88"  y1="253" x2="87"  y2="261" stroke="#d8a878" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="112" y1="255" x2="113" y2="262" stroke="#d8a878" stroke-width="0.7" stroke-linecap="round"/>
        <line x1="117" y1="253" x2="118" y2="261" stroke="#d8a878" stroke-width="0.7" stroke-linecap="round"/>
      </g>
    </g>
    <!-- Head -->
    <g id="avatar-head" style="transform-origin:100px 130px">
      <g id="avatar-hair">
        <!-- Short white curled hair base -->
        <ellipse cx="100" cy="97" rx="29" ry="28" fill="#d0d0d8"/>
        <!-- Curl bumps on top -->
        <ellipse cx="88"  cy="84" rx="8" ry="6"  fill="#d0d0d8"/>
        <ellipse cx="100" cy="82" rx="9" ry="7"  fill="#d0d0d8"/>
        <ellipse cx="112" cy="84" rx="8" ry="6"  fill="#d0d0d8"/>
        <!-- Side puffs -->
        <ellipse cx="71"  cy="104" rx="8"  ry="10" fill="#d0d0d8"/>
        <ellipse cx="129" cy="104" rx="8"  ry="10" fill="#d0d0d8"/>
        <!-- Curl highlight details -->
        <path d="M84 84 Q88 80 92 84" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M98 82 Q102 78 106 82" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M84 89 Q88 85 92 89" fill="none" stroke="rgba(255,255,255,0.30)" stroke-width="1.2" stroke-linecap="round"/>
      </g>
      <rect x="92" y="133" width="16" height="20" rx="4" fill="url(#g-skin)"/>
      <line x1="92" y1="139" x2="108" y2="139" stroke="rgba(0,0,0,0.09)" stroke-width="2"/>
      <ellipse id="avatar-head-shape" cx="100" cy="107" rx="26" ry="32" fill="url(#g-skin-face)"/>
      <ellipse cx="74"  cy="110" rx="4.5" ry="6.5" fill="url(#g-skin)"/>
      <ellipse cx="74"  cy="110" rx="2.1" ry="3.8" fill="#d8a878"/>
      <ellipse cx="126" cy="110" rx="4.5" ry="6.5" fill="url(#g-skin)"/>
      <ellipse cx="126" cy="110" rx="2.1" ry="3.8" fill="#d8a878"/>
      <g id="avatar-face">
        <g id="avatar-brow">
          <!-- Light, thin elder brows -->
          <path d="M83 93 Q88 91 94 93" fill="none" stroke="#b0a090" stroke-width="1.4" stroke-linecap="round"/>
          <path d="M106 93 Q112 91 117 93" fill="none" stroke="#b0a090" stroke-width="1.4" stroke-linecap="round"/>
        </g>
        <g id="avatar-eyes">
          <ellipse cx="88"  cy="107" rx="8.5" ry="7.5" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="112" cy="107" rx="8.5" ry="7.5" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="88"  cy="107" rx="6.8" ry="5.5" fill="#fff"/>
          <ellipse cx="112" cy="107" rx="6.8" ry="5.5" fill="#fff"/>
          <circle  cx="88"  cy="107" r="3.4" fill="#808898"/>
          <circle  cx="112" cy="107" r="3.4" fill="#808898"/>
          <circle  cx="88"  cy="107" r="1.8" fill="#1a1a28"/>
          <circle  cx="112" cy="107" r="1.8" fill="#1a1a28"/>
          <circle  cx="89.5"  cy="105.5" r="0.9" fill="rgba(255,255,255,0.65)"/>
          <circle  cx="113.5" cy="105.5" r="0.9" fill="rgba(255,255,255,0.65)"/>
          <path d="M81 104 Q88 101 95 104" fill="none" stroke="#c0a080" stroke-width="0.7" stroke-linecap="round"/>
          <path d="M105 104 Q112 101 119 104" fill="none" stroke="#c0a080" stroke-width="0.7" stroke-linecap="round"/>
        </g>
        <g id="avatar-nose">
          <path d="M100 110 Q97 116 96 118 Q100 121 104 118 Q103 116 100 110Z"
                fill="none" stroke="#c0a080" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
          <ellipse cx="96.5"  cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
          <ellipse cx="103.5" cy="118.5" rx="2.2" ry="1.4" fill="rgba(0,0,0,0.08)"/>
        </g>
        <!-- Wrinkle lines -->
        <path d="M84 90 Q100 88 116 90" fill="none" stroke="rgba(160,120,80,0.15)" stroke-width="0.9" stroke-linecap="round"/>
        <path d="M81 110 Q78 113 80 116" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.7" stroke-linecap="round"/>
        <path d="M119 110 Q122 113 120 116" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.7" stroke-linecap="round"/>
        <path d="M91 118 Q89 124 91 128" fill="none" stroke="rgba(160,120,80,0.16)" stroke-width="0.7" stroke-linecap="round"/>
        <path d="M109 118 Q111 124 109 128" fill="none" stroke="rgba(160,120,80,0.16)" stroke-width="0.7" stroke-linecap="round"/>
        <g id="avatar-jaw" style="transform-origin:100px 126px">
          <path d="M76 120 Q79 136 100 142 Q121 136 124 120" fill="url(#g-skin-face)" stroke="none"/>
          <ellipse cx="100" cy="139" rx="5.5" ry="2.2" fill="rgba(255,255,255,0.11)"/>
          <path id="avatar-mouth" d="M91 126 Q100 131 109 126" fill="none"
                stroke="#b08878" stroke-width="1.7" stroke-linecap="round"/>
          <path d="M98 122 Q100 124 102 122" fill="none" stroke="#c0a088"
                stroke-width="0.8" stroke-linecap="round"/>
        </g>
        <g id="avatar-tear" opacity="0">
          <ellipse cx="85"  cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
          <ellipse cx="115" cy="114" rx="2" ry="3" fill="rgba(180,210,255,0.85)"/>
        </g>
      </g>
    </g>
  </g>`
  );

})();
