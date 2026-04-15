#!/usr/bin/env python3
"""
DFC Friction Friday Content Generator
======================================
Setup:
  pip install flask anthropic duckduckgo-search

Run:
  python friction_friday_generator.py

Then open http://localhost:5000 in your browser.
"""

import os
import json
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a content writer for Dynamic Friction Company (DFC), creating scripts and YouTube descriptions for the "Friction Friday" video series.

## Script Rules (~80–110 words)
1. Always open with exactly: "Hi everyone. This week on Friction Friday, we have the [YEAR(S)] [MAKE] [MODEL]."
2. Write 1–2 sentences on the vehicle's character, purpose, or what makes it distinctive — research the vehicle and tailor this to the actual car.
3. Mention "DFC's 5000 Series Advanced Brake Pads and GeoSpec Coated Rotors" with 2 relevant benefits.
4. Add one sentence about GeoSpec corrosion resistance and OE-specific fitment.
5. Close with: "DFC [proudly] supports the [MODEL] with a complete braking solution."

## Description Rules (exactly 2 sentences, ~40–55 words)
1. "[YEAR(S)] [MAKE] [MODEL] [character hook], making [braking adjective] braking essential."
2. "The DFC 5000 Brake Kit with GeoSpec Rotors [delivers/provides] OE-level fit, [benefit 1], and [benefit 2]."

## Year Formatting
- Single year: "2026 Toyota C-HR"
- Range (in script body): "2023 through 2026 Toyota GR Corolla"
- Range (in description): "2023–2026 Toyota GR Corolla" (use en-dash)

## Benefit Language by Vehicle Type
- Performance/Sports: "strong initial bite", "stable performance under aggressive driving conditions", "precise control"
- Luxury: "smooth pedal response", "quiet operation", "refined stopping"
- EV/Hybrid: reference "regenerative systems" and/or "increased weight", use "stable pedal feel"
- Family/SUV: "dependable braking", "smooth pedal feel", "consistent stopping performance"
- Crossover: "confident bite", "smooth pedal feel", "quiet performance"

## All Existing Scripts (match this tone exactly)

PERFORMANCE — 2023 through 2026 Toyota GR Corolla:
"Hi everyone. This week on Friction Friday, we have the 2023 through 2026 Toyota GR Corolla. Built for performance enthusiasts, the GR Corolla brings rally-inspired engineering, turbocharged power, and all-wheel-drive capability into a compact hatchback. With that level of responsiveness, braking needs to be just as sharp, delivering control you can feel in every corner and every stop. DFC's 5000 Series Advanced Brake Pads and GeoSpec Coated Rotors are engineered to meet OE specifications, providing strong initial bite, consistent pedal feel, and stable performance under aggressive driving conditions. GeoSpec coated rotors offer corrosion resistance while OE-specific designs ensure precise fitment. DFC proudly supports the GR Corolla with a complete braking solution."

LUXURY — 2023 through 2026 Maserati Grecale:
"Hi everyone. This week on Friction Friday, we have the 2023 through 2026 Maserati Grecale. Blending Italian craftsmanship with modern performance, the Grecale delivers a refined yet responsive driving experience. DFC's 5000 Series Advanced Brake Pads and GeoSpec Coated Rotors help maintain smooth pedal response and quiet operation. GeoSpec coated rotors provide corrosion resistance while OE-specific fitment ensures precise installation. DFC supports the Grecale with a complete braking solution."

COMPACT CROSSOVER — 2026 Toyota C-HR:
"Hi everyone. This week on Friction Friday, we have the 2026 Toyota C-HR. With bold styling and agile handling, the C-HR is built for responsive driving. DFC's 5000 Series Advanced Brake Pads and GeoSpec Coated Rotors deliver confident bite, smooth pedal feel, and quiet performance. GeoSpec coatings provide corrosion resistance while OE-specific fitment ensures easy installation. DFC supports the C-HR with a complete braking solution."

EV — 2024 through 2026 Acura ZDX:
"Hi everyone. This week on Friction Friday, we have the 2024 through 2026 Acura ZDX. As an all-electric luxury SUV, the ZDX requires braking components that handle regenerative systems and increased weight. DFC's 5000 Series pads and GeoSpec rotors deliver stable pedal feel and quiet operation. GeoSpec coating protects against corrosion while OE-specific fitment ensures accurate installation."

FAMILY SUV — 2027 Kia Telluride:
"Hi everyone. This week on Friction Friday, we have the 2027 Kia Telluride. Built for families and versatility, the Telluride requires dependable braking for daily driving. DFC's 5000 Series pads and GeoSpec rotors provide smooth pedal feel and consistent stopping performance. GeoSpec coatings help resist corrosion while OE-specific fitment ensures easy installation."

## Output Format
Return ONLY valid JSON with exactly these two keys, no extra text:
{
  "script": "...",
  "description": "..."
}
"""


def generate_content(year_start: str, year_end: str, make: str, model: str, api_key: str):
    """Call Claude API to generate the script and description."""
    if year_end and year_end != year_start:
        year_spoken = f"{year_start} through {year_end}"
        year_display = f"{year_start}–{year_end}"
    else:
        year_spoken = year_start
        year_display = year_start

    user_prompt = (
        f"Generate a Friction Friday script and YouTube description for the "
        f"{year_spoken} {make} {model}. "
        f"Use '{year_spoken}' in the script body and '{year_display}' in the description. "
        f"Research this vehicle's actual character and tailor the content accordingly."
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)
    return result["script"], result["description"]


def search_images(year_start: str, year_end: str, make: str, model: str) -> list:
    """Search DuckDuckGo for vehicle images and return a list of URLs."""
    try:
        from duckduckgo_search import DDGS
        year = year_end if year_end else year_start
        queries = [
            f"{year} {make} {model} exterior official",
            f"{year} {make} {model} press photo",
        ]
        images = []
        seen = set()
        with DDGS() as ddgs:
            for q in queries:
                if len(images) >= 9:
                    break
                results = ddgs.images(q, max_results=9)
                for r in results:
                    url = r.get("image", "")
                    if url and url not in seen:
                        images.append(url)
                        seen.add(url)
                    if len(images) >= 9:
                        break
        return images
    except Exception as e:
        print(f"[image search] {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DFC Friction Friday Generator</title>
<style>
  :root {
    --blue: #00285e;
    --blue-mid: #1a5fa8;
    --orange: #e8640a;
    --orange-hover: #cf5708;
    --bg: #f0f3f8;
    --white: #ffffff;
    --border: #dde3ec;
    --text: #111827;
    --muted: #6b7280;
    --green: #16a34a;
    --red-bg: #fef2f2;
    --red-border: #fecaca;
    --red-text: #991b1b;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: var(--blue);
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
  }
  .logo-dfc {
    color: var(--orange);
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 1px;
    line-height: 1;
  }
  .logo-divider { width: 1px; height: 28px; background: rgba(255,255,255,0.2); }
  .logo-title { color: #fff; font-size: 17px; font-weight: 600; }
  .logo-sub { color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 1px; }

  /* ── Layout ── */
  .container { max-width: 920px; margin: 0 auto; padding: 32px 20px 60px; }

  /* ── Cards ── */
  .card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 26px 28px;
    margin-bottom: 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .card-title {
    font-size: 11px;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 18px;
  }

  /* ── Form ── */
  .form-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 14px; margin-bottom: 18px; }
  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .field label .optional { font-weight: 400; text-transform: none; font-size: 10px; }
  .field input {
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 10px 13px;
    font-size: 15px;
    color: var(--text);
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    background: #fafbfc;
  }
  .field input:focus {
    border-color: var(--blue-mid);
    background: var(--white);
    box-shadow: 0 0 0 3px rgba(26,95,168,0.12);
  }

  .api-row { display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: end; }
  .api-note { font-size: 11px; color: var(--muted); margin-top: 5px; }

  /* ── Generate Button ── */
  .btn-generate {
    background: var(--orange);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 11px 26px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
    box-shadow: 0 2px 6px rgba(232,100,10,0.35);
  }
  .btn-generate:hover { background: var(--orange-hover); box-shadow: 0 3px 10px rgba(232,100,10,0.45); }
  .btn-generate:active { transform: scale(0.97); }
  .btn-generate:disabled { background: #bbb; box-shadow: none; cursor: not-allowed; transform: none; }

  /* ── Error ── */
  .error-msg {
    background: var(--red-bg);
    border: 1px solid var(--red-border);
    color: var(--red-text);
    border-radius: 8px;
    padding: 11px 15px;
    font-size: 13px;
    margin-top: 14px;
    display: none;
  }
  .error-msg.show { display: block; }

  /* ── Loading ── */
  .loading {
    display: none;
    align-items: center;
    gap: 12px;
    color: var(--muted);
    font-size: 14px;
    padding: 10px 0 6px;
  }
  .loading.show { display: flex; }
  .spinner {
    width: 22px; height: 22px;
    border: 2.5px solid var(--border);
    border-top-color: var(--blue);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Result Cards ── */
  .result-section { display: none; }
  .result-section.show { display: block; }

  .result-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .result-header {
    background: var(--blue);
    padding: 13px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .result-header h3 {
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .vehicle-tag {
    background: var(--orange);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 20px;
    letter-spacing: 0;
    text-transform: none;
  }
  .btn-copy {
    background: rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.9);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    flex-shrink: 0;
  }
  .btn-copy:hover { background: rgba(255,255,255,0.22); }
  .btn-copy.copied { background: var(--green); border-color: var(--green); }

  .result-body { padding: 20px 22px; }
  .result-text {
    font-size: 15px;
    line-height: 1.75;
    color: var(--text);
    white-space: pre-wrap;
    font-family: inherit;
  }

  /* ── Images ── */
  .images-wrap {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .images-header {
    background: var(--blue);
    padding: 13px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .images-header h3 {
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
  }
  .images-header span { color: rgba(255,255,255,0.5); font-size: 11px; }

  .image-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 14px;
  }
  .image-item {
    aspect-ratio: 16/9;
    border-radius: 7px;
    overflow: hidden;
    cursor: pointer;
    background: #e8edf4;
    position: relative;
  }
  .image-item img {
    width: 100%; height: 100%;
    object-fit: cover;
    transition: transform 0.2s;
    display: block;
  }
  .image-item:hover img { transform: scale(1.05); }
  .img-overlay {
    position: absolute; inset: 0;
    background: rgba(0,40,94,0.55);
    display: flex; align-items: center; justify-content: center;
    opacity: 0;
    transition: opacity 0.18s;
  }
  .image-item:hover .img-overlay { opacity: 1; }
  .img-overlay svg { color: #fff; }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .form-grid { grid-template-columns: 1fr 1fr; }
    .api-row { grid-template-columns: 1fr; }
    .btn-generate { width: 100%; justify-content: center; }
    .image-grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>

<header>
  <div>
    <div class="logo-dfc">DFC</div>
    <div class="logo-sub">Dynamic Friction Company</div>
  </div>
  <div class="logo-divider"></div>
  <div>
    <div class="logo-title">Friction Friday Generator</div>
  </div>
</header>

<div class="container">

  <!-- Input Card -->
  <div class="card">
    <div class="card-title">Vehicle Details</div>

    <div class="form-grid">
      <div class="field">
        <label>Year Start</label>
        <input type="number" id="year_start" placeholder="2024" min="1990" max="2035">
      </div>
      <div class="field">
        <label>Year End <span class="optional">(optional)</span></label>
        <input type="number" id="year_end" placeholder="2026" min="1990" max="2035">
      </div>
      <div class="field">
        <label>Make</label>
        <input type="text" id="make" placeholder="Toyota">
      </div>
      <div class="field">
        <label>Model</label>
        <input type="text" id="model" placeholder="GR Corolla">
      </div>
    </div>

    <div class="api-row">
      <div class="field">
        <label>Anthropic API Key</label>
        <input type="password" id="api_key" placeholder="sk-ant-api03-...">
        <div class="api-note">Saved in your browser. Never sent anywhere except Anthropic's API.</div>
      </div>
      <button class="btn-generate" id="gen_btn" onclick="generate()">
        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
        Generate
      </button>
    </div>

    <div class="error-msg" id="error_msg"></div>
  </div>

  <!-- Loading -->
  <div class="loading" id="loading">
    <div class="spinner"></div>
    <span>Generating script &amp; description, searching for images…</span>
  </div>

  <!-- Results -->
  <div class="result-section" id="results">

    <div class="result-card">
      <div class="result-header">
        <h3>Video Script <span class="vehicle-tag" id="vehicle_tag"></span></h3>
        <button class="btn-copy" onclick="copyText('script_text', this)">Copy</button>
      </div>
      <div class="result-body">
        <div class="result-text" id="script_text"></div>
      </div>
    </div>

    <div class="result-card">
      <div class="result-header">
        <h3>YouTube Description</h3>
        <button class="btn-copy" onclick="copyText('desc_text', this)">Copy</button>
      </div>
      <div class="result-body">
        <div class="result-text" id="desc_text"></div>
      </div>
    </div>

    <div class="images-wrap" id="images_wrap">
      <div class="images-header">
        <h3>Vehicle Images</h3>
        <span>Click any image to open full size</span>
      </div>
      <div class="image-grid" id="image_grid"></div>
    </div>

  </div><!-- /results -->

</div><!-- /container -->

<script>
  // Restore API key
  window.onload = () => {
    const k = localStorage.getItem('dfc_ff_api_key');
    if (k) document.getElementById('api_key').value = k;
  };

  async function generate() {
    const yearStart = document.getElementById('year_start').value.trim();
    const yearEnd   = document.getElementById('year_end').value.trim();
    const make      = document.getElementById('make').value.trim();
    const model     = document.getElementById('model').value.trim();
    const apiKey    = document.getElementById('api_key').value.trim();
    const errEl     = document.getElementById('error_msg');

    errEl.classList.remove('show');

    if (!yearStart || !make || !model) {
      errEl.textContent = 'Please fill in Year Start, Make, and Model.';
      errEl.classList.add('show');
      return;
    }
    if (!apiKey) {
      errEl.textContent = 'Please enter your Anthropic API key.';
      errEl.classList.add('show');
      return;
    }

    localStorage.setItem('dfc_ff_api_key', apiKey);

    document.getElementById('loading').classList.add('show');
    document.getElementById('results').classList.remove('show');
    document.getElementById('gen_btn').disabled = true;

    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ year_start: yearStart, year_end: yearEnd, make, model, api_key: apiKey })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Generation failed.');

      // Populate text
      document.getElementById('script_text').textContent = data.script;
      document.getElementById('desc_text').textContent   = data.description;

      // Vehicle badge
      const hasRange = yearEnd && yearEnd !== yearStart;
      document.getElementById('vehicle_tag').textContent =
        (hasRange ? `${yearStart}–${yearEnd}` : yearStart) + ` ${make} ${model}`;

      // Images
      const grid = document.getElementById('image_grid');
      grid.innerHTML = '';
      const imgs = (data.images || []).filter(Boolean);

      if (imgs.length) {
        imgs.forEach(url => {
          const div = document.createElement('div');
          div.className = 'image-item';
          div.innerHTML = `
            <img src="${url}" alt="Vehicle photo"
                 onerror="this.closest('.image-item').style.display='none'">
            <div class="img-overlay">
              <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </div>`;
          div.onclick = () => window.open(url, '_blank');
          grid.appendChild(div);
        });
        document.getElementById('images_wrap').style.display = '';
      } else {
        document.getElementById('images_wrap').style.display = 'none';
      }

      document.getElementById('results').classList.add('show');
      document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.add('show');
    } finally {
      document.getElementById('loading').classList.remove('show');
      document.getElementById('gen_btn').disabled = false;
    }
  }

  function copyText(id, btn) {
    const text = document.getElementById(id).textContent;
    navigator.clipboard.writeText(text).then(() => {
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
    });
  }

  // Cmd/Ctrl+Enter to generate
  document.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) generate();
  });
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True) or {}
    year_start = str(data.get("year_start", "")).strip()
    year_end   = str(data.get("year_end",   "")).strip()
    make       = str(data.get("make",       "")).strip()
    model      = str(data.get("model",      "")).strip()
    api_key    = str(data.get("api_key",    "")).strip() or os.environ.get("ANTHROPIC_API_KEY", "")

    if not all([year_start, make, model, api_key]):
        return jsonify({"error": "Missing required fields."}), 400

    try:
        script, description = generate_content(year_start, year_end, make, model, api_key)
        images = search_images(year_start, year_end, make, model)
        return jsonify({"script": script, "description": description, "images": images})

    except anthropic.AuthenticationError:
        return jsonify({"error": "Invalid API key. Please check your Anthropic API key."}), 401
    except json.JSONDecodeError:
        return jsonify({"error": "Unexpected response from AI model — please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  DFC Friction Friday Generator")
    print("  ─────────────────────────────")
    print("  Open in your browser: http://localhost:5000")
    print("  Press Ctrl+C to stop.")
    print()
    app.run(host="0.0.0.0", port=5000, debug=False)
