#!/usr/bin/env python3
"""
Scrape status Spaces & Models Hugging Face (via API resmi, bukan HTML scraping)
lalu suntikkan hasilnya sebagai tabel Markdown ke dalam README.md,
di antara marker <!-- HF-ACTIVITY:START --> ... <!-- HF-ACTIVITY:END -->.

Dijalankan otomatis oleh GitHub Actions (lihat .github/workflows/update-hf-status.yml)
supaya tampilan "real-time" tanpa perlu commit manual.
"""

import os
import sys
from datetime import datetime, timezone

import requests

HF_USERNAME = os.environ.get("HF_USERNAME", "maftuh-main")
README_PATH = os.environ.get("README_PATH", "README.md")

START_MARKER = "<!-- HF-ACTIVITY:START -->"
END_MARKER = "<!-- HF-ACTIVITY:END -->"

STAGE_EMOJI = {
    "RUNNING": "🟢 Running",
    "RUNNING_BUILDING": "🟡 Building",
    "BUILDING": "🟡 Building",
    "SLEEPING": "😴 Sleeping",
    "STOPPED": "⏹️ Stopped",
    "PAUSED": "⏸️ Paused",
    "RUNTIME_ERROR": "🔴 Error",
}


def fetch_spaces(username: str) -> list[dict]:
    url = f"https://huggingface.co/api/spaces?author={username}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    spaces = r.json()
    
    # Fetch detail untuk tiap space agar mendapatkan info 'runtime' (status SLEEPING/RUNNING dsb)
    for s in spaces:
        space_id = s.get("id")
        if space_id:
            try:
                detail_r = requests.get(f"https://huggingface.co/api/spaces/{space_id}", timeout=10)
                if detail_r.status_code == 200:
                    s["runtime"] = detail_r.json().get("runtime", {})
            except Exception:
                pass
                
    return spaces


def fetch_models(username: str) -> list[dict]:
    url = f"https://huggingface.co/api/models?author={username}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def pad_right(text: str, length: int) -> str:
    # Mengatasi masalah padding dengan karakter emoji yang lebarnya beda
    # Kita asumsikan emoji di status memakan 1 atau 2 karakter tambahan visual
    return text.ljust(length)

def build_spaces_table(spaces: list[dict]) -> str:
    if not spaces:
        return "  _Belum ada Space yang terdeteksi._"

    # Menghitung lebar kolom
    max_name = max(len(s.get("id", "").split("/")[-1]) for s in spaces)
    max_name = max(max_name, 45) # Minimal 45 agar tabel lebih lebar
    
    status_w = 15
    likes_w = 10
    sdk_w = 12
    
    rows = [
        f"+-{'-' * max_name}-+-{'-' * status_w}-+-{'-' * likes_w}-+-{'-' * sdk_w}-+",
        f"| {'Name'.ljust(max_name)} | {'Status'.ljust(status_w)} | {'Likes'.ljust(likes_w)} | {'SDK'.ljust(sdk_w)} |",
        f"+-{'-' * max_name}-+-{'-' * status_w}-+-{'-' * likes_w}-+-{'-' * sdk_w}-+",
    ]
    
    for s in spaces:
        stage = s.get("runtime", {}).get("stage", "UNKNOWN")
        status_label = STAGE_EMOJI.get(stage, f"⚪ {stage}")
        name = s.get("id", "").split("/")[-1]
        likes = str(s.get("likes", 0))
        sdk = s.get("sdk", "-")
        
        # Karena emoji 'status_label' makan space ekstra di visual, ljust butuh disesuaikan
        # Biasanya terminal modern akan menyesuaikan tapi monospace di web kadang sedikit meleset
        rows.append(f"| {name.ljust(max_name)} | {status_label.ljust(status_w)} | {likes.rjust(likes_w)} | {sdk.ljust(sdk_w)} |")
        
    rows.append(f"+-{'-' * max_name}-+-{'-' * status_w}-+-{'-' * likes_w}-+-{'-' * sdk_w}-+")
    return "\n".join(rows)


def build_models_table(models: list[dict]) -> str:
    if not models:
        return "  _Belum ada Model yang terdeteksi._"

    max_name = max(len(m.get("id", "").split("/")[-1]) for m in models)
    max_name = max(max_name, 45) # Minimal 45 agar seimbang dengan spaces
    
    dl_w = 15
    likes_w = 10
    
    rows = [
        f"+-{'-' * max_name}-+-{'-' * dl_w}-+-{'-' * likes_w}-+",
        f"| {'Name'.ljust(max_name)} | {'Downloads'.ljust(dl_w)} | {'Likes'.ljust(likes_w)} |",
        f"+-{'-' * max_name}-+-{'-' * dl_w}-+-{'-' * likes_w}-+",
    ]
    
    for m in models:
        name = m.get("id", "").split("/")[-1]
        downloads = str(m.get("downloads", 0))
        likes = str(m.get("likes", 0))
        rows.append(f"| {name.ljust(max_name)} | {downloads.rjust(dl_w)} | {likes.rjust(likes_w)} |")
        
    rows.append(f"+-{'-' * max_name}-+-{'-' * dl_w}-+-{'-' * likes_w}-+")
    return "\n".join(rows)


from collections import Counter
import os
import math

def _compute_rank(models_count, spaces_count, downloads, likes):
    """Compute a rank grade based on HF activity."""
    score = models_count * 10 + spaces_count * 15 + downloads * 0.05 + likes * 20
    if score >= 500: return "S+"
    if score >= 200: return "S"
    if score >= 100: return "A++"
    if score >= 50:  return "A+"
    if score >= 25:  return "A"
    if score >= 10:  return "B+"
    return "B"

def _rank_progress(models_count, spaces_count, downloads, likes):
    """Return 0-100 progress toward next rank."""
    score = models_count * 10 + spaces_count * 15 + downloads * 0.05 + likes * 20
    thresholds = [10, 25, 50, 100, 200, 500]
    for t in thresholds:
        if score < t:
            prev = thresholds[thresholds.index(t) - 1] if thresholds.index(t) > 0 else 0
            return int(((score - prev) / (t - prev)) * 100)
    return 100

def generate_stats_svg(models_count, spaces_count, downloads, likes) -> str:
    rank = _compute_rank(models_count, spaces_count, downloads, likes)
    progress = _rank_progress(models_count, spaces_count, downloads, likes)
    # Circle math: r=40, circumference = 2*pi*40 ≈ 251.3
    circ = 2 * math.pi * 40
    dash = circ * progress / 100
    gap = circ - dash

    return f"""<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="border-grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFD21E" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#FF9D00" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFD21E"/>
      <stop offset="100%" stop-color="#FF9D00"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e6e6e6; }}
    .stat-label {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
    .stat-value {{ font: 700 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .rank-text {{ font: 800 28px 'Segoe UI', Ubuntu, Sans-Serif; fill: url(#ring-grad); }}
    .rank-label {{ font: 500 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes rankPulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.8; }} }}
    .stats-group {{ animation: fadeIn 0.8s ease-in-out; }}
    .rank-circle {{ animation: rankPulse 3s ease-in-out infinite; }}
  </style>

  <rect x="0.5" y="0.5" rx="4.5" width="494" height="194" fill="#0d1117" stroke="url(#border-grad)" stroke-width="1"/>

  <g transform="translate(25, 35)">
    <text x="0" y="0" class="header">🤗 Hugging Face Statistics</text>
  </g>

  <g class="stats-group" transform="translate(30, 62)">
    <g transform="translate(0, 0)">
      <circle cx="6" cy="-4" r="5" fill="#FFD21E" opacity="0.2"/>
      <circle cx="6" cy="-4" r="2" fill="#FFD21E"/>
      <text x="18" y="0" class="stat-label">Total Models:</text>
      <text x="140" y="0" class="stat-value">{models_count}</text>
    </g>
    <g transform="translate(0, 28)">
      <circle cx="6" cy="-4" r="5" fill="#58a6ff" opacity="0.2"/>
      <circle cx="6" cy="-4" r="2" fill="#58a6ff"/>
      <text x="18" y="0" class="stat-label">Total Spaces:</text>
      <text x="140" y="0" class="stat-value">{spaces_count}</text>
    </g>
    <g transform="translate(0, 56)">
      <circle cx="6" cy="-4" r="5" fill="#3fb950" opacity="0.2"/>
      <circle cx="6" cy="-4" r="2" fill="#3fb950"/>
      <text x="18" y="0" class="stat-label">Total Downloads:</text>
      <text x="140" y="0" class="stat-value">{downloads:,}</text>
    </g>
    <g transform="translate(0, 84)">
      <circle cx="6" cy="-4" r="5" fill="#f778ba" opacity="0.2"/>
      <circle cx="6" cy="-4" r="2" fill="#f778ba"/>
      <text x="18" y="0" class="stat-label">Total Likes:</text>
      <text x="140" y="0" class="stat-value">{likes}</text>
    </g>
  </g>

  <g class="rank-circle" transform="translate(370, 55)" filter="url(#glow)">
    <circle cx="50" cy="50" r="40" fill="none" stroke="#21262d" stroke-width="6"/>
    <circle cx="50" cy="50" r="40" fill="none" stroke="url(#ring-grad)" stroke-width="6"
            stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round"
            transform="rotate(-90 50 50)"/>
    <text x="50" y="48" class="rank-text" text-anchor="middle" dominant-baseline="middle">{rank}</text>
    <text x="50" y="72" class="rank-label" text-anchor="middle">rank</text>
  </g>
</svg>"""


def generate_tags_svg(models, spaces) -> str:
    tags = []
    for item in models + spaces:
        t = item.get("tags", [])
        if isinstance(t, list):
            tags.extend([x for x in t if ":" not in x and x not in (
                "safetensors", "endpoints_compatible", "transformers", "region:us",
                "text-generation-inference", "conversational", "id"
            )])

    counter = Counter(tags)
    top_tags = counter.most_common(8)

    if not top_tags:
        top_tags = [("N/A", 1)]

    total_tags = sum(count for _, count in top_tags)
    colors = ["#3178c6", "#00b4ab", "#e34c26", "#4f5b93", "#178600",
              "#f1e05a", "#563d7c", "#b07219"]

    # Build the horizontal stacked bar (top)
    bar_width = 245
    bar_segments = ""
    bar_x = 0
    for i, (tag, count) in enumerate(top_tags):
        w = (count / total_tags) * bar_width
        color = colors[i % len(colors)]
        bar_segments += f'<rect x="{bar_x:.1f}" y="0" width="{w:.1f}" height="8" rx="0" fill="{color}"/>'
        bar_x += w
    # Round the ends
    bar_segments = f'<clipPath id="bar-clip"><rect x="0" y="0" width="{bar_width}" height="8" rx="4"/></clipPath><g clip-path="url(#bar-clip)">{bar_segments}</g>'

    # Build legend (2 columns)
    legend = ""
    col1_x = 0
    col2_x = 130
    y = 0
    for i, (tag, count) in enumerate(top_tags):
        perc = (count / total_tags) * 100
        color = colors[i % len(colors)]
        x = col1_x if i % 2 == 0 else col2_x
        if i % 2 == 0 and i > 0:
            y += 22
        legend += f'''<g transform="translate({x}, {y})">
      <circle cx="5" cy="-4" r="5" fill="{color}" opacity="0.2"/>
      <circle cx="5" cy="-4" r="2.5" fill="{color}"/>
      <text x="14" y="0" class="tag-name">{tag} ({perc:.0f}%)</text>
    </g>'''

    return f"""<svg width="310" height="195" viewBox="0 0 310 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="border-grad2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFD21E" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#FF9D00" stop-opacity="0.3"/>
    </linearGradient>
  </defs>
  <style>
    .header2 {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e6e6e6; }}
    .tag-name {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #c9d1d9; }}
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    .tag-group {{ animation: fadeIn 0.8s ease-in-out; }}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="309" height="194" fill="#0d1117" stroke="url(#border-grad2)" stroke-width="1"/>
  <text x="25" y="35" class="header2">My ML / AI Focus Areas</text>
  <g class="tag-group" transform="translate(30, 55)">
    {bar_segments}
  </g>
  <g class="tag-group" transform="translate(30, 80)">
    {legend}
  </g>
</svg>"""

def build_block(username: str) -> str:
    spaces = fetch_spaces(username)
    models = fetch_models(username)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    total_models = len(models)
    total_spaces = len(spaces)
    total_downloads = sum(m.get("downloads", 0) for m in models)
    total_likes = sum(m.get("likes", 0) for m in models) + sum(s.get("likes", 0) for s in spaces)

    os.makedirs("assets", exist_ok=True)
    with open("assets/hf-stats.svg", "w", encoding="utf-8") as f:
        f.write(generate_stats_svg(total_models, total_spaces, total_downloads, total_likes))
    with open("assets/hf-tags.svg", "w", encoding="utf-8") as f:
        f.write(generate_tags_svg(models, spaces))

    badges = (
        f'<div align="center">\n'
        f'  <img src="assets/hf-stats.svg" alt="Hugging Face Statistics" />\n'
        f'  <img src="assets/hf-tags.svg" alt="Top ML Tags" />\n'
        f'</div>\n'
    )

    block = [
        START_MARKER,
        badges,
        "```console",
        f"maftuh@hf-api:~$ ./fetch_hf_stats.sh --user {username}",
        "[+] Fetching Hugging Face activity... Done!",
        f"[+] Last updated: {now}",
        "",
        "🚀 SPACES",
        build_spaces_table(spaces),
        "",
        "🧠 MODELS",
        build_models_table(models),
        "```",
        END_MARKER,
    ]
    return "\n".join(block)


def inject_into_readme(readme_path: str, block: str) -> bool:
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        print(
            f"Marker {START_MARKER} / {END_MARKER} tidak ditemukan di {readme_path}.\n"
            "Tambahkan dulu kedua marker itu di README, lalu jalankan ulang script ini.",
            file=sys.stderr,
        )
        return False

    pre = content.split(START_MARKER)[0]
    post = content.split(END_MARKER)[1]
    new_content = pre + block + post

    if new_content == content:
        print("Tidak ada perubahan.")
        return False

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README diperbarui.")
    return True


def main() -> None:
    block = build_block(HF_USERNAME)
    changed = inject_into_readme(README_PATH, block)
    # exit code 0 = ada perubahan (dipakai workflow untuk memutuskan commit atau tidak)
    sys.exit(0 if changed else 78)


if __name__ == "__main__":
    main()
