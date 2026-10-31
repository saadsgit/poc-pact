"""Inline brand assets kept as code so they stay crisp and dependency-free."""

# Hexagon outline with an arrow breaking upward through it:
# the loop of a connection turning into an outcome.
LOGO_SVG = """
<svg viewBox="0 0 64 64" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="POC Pact logo">
  <defs>
    <linearGradient id="pp-hex" x1="10" y1="8" x2="54" y2="58" gradientUnits="userSpaceOnUse">
      <stop stop-color="#9df27a"/>
      <stop offset="1" stop-color="#15924a"/>
    </linearGradient>
    <linearGradient id="pp-arrow" x1="20" y1="54" x2="52" y2="14" gradientUnits="userSpaceOnUse">
      <stop stop-color="#1c7a3c"/>
      <stop offset="1" stop-color="#52e08a"/>
    </linearGradient>
  </defs>
  <path d="M32 7 54 19.5V44.5L32 57 10 44.5V19.5Z"
        stroke="url(#pp-hex)" stroke-width="5.4" stroke-linejoin="round" fill="none"/>
  <path d="M22 55 44 20"
        stroke="url(#pp-arrow)" stroke-width="7.2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M33 17 L49 15 L47 31"
        stroke="url(#pp-arrow)" stroke-width="7.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
"""
