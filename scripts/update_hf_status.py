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

def generate_stats_svg(models_count, spaces_count, downloads, likes) -> str:
    return f"""<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #aaaaaa; }}
    .stat {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .icon {{ fill: #888888; font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif; }}
    .bold {{ font-weight: 700; }}
  </style>
  <rect x="0.5" y="0.5" rx="20" width="494" height="194" fill="#0d1117" stroke="#e4e2e2" stroke-opacity="0" />
  <text x="25" y="35" class="header">My Hugging Face Statistics</text>
  
  <g transform="translate(25, 65)">
    <text x="0" y="0" class="stat">📦</text>
    <text x="30" y="0" class="stat">Total Models:</text>
    <text x="170" y="0" class="stat bold">{models_count}</text>
    
    <text x="0" y="30" class="stat">🚀</text>
    <text x="30" y="30" class="stat">Total Spaces:</text>
    <text x="170" y="30" class="stat bold">{spaces_count}</text>
    
    <text x="0" y="60" class="stat">⬇️</text>
    <text x="30" y="60" class="stat">Total Downloads:</text>
    <text x="170" y="60" class="stat bold">{downloads}</text>
    
    <text x="0" y="90" class="stat">❤️</text>
    <text x="30" y="90" class="stat">Total Likes:</text>
    <text x="170" y="90" class="stat bold">{likes}</text>
  </g>
  
  <g transform="translate(360, 60)">
    <circle cx="50" cy="50" r="40" fill="none" stroke="#FFD21E" stroke-width="6" />
    <text x="50" y="55" font-size="35" fill="#FFD21E" text-anchor="middle" dominant-baseline="middle" font-family="'Segoe UI Emoji', sans-serif">🤗</text>
  </g>
</svg>"""

def generate_tags_svg(models, spaces) -> str:
    tags = []
    for item in models + spaces:
        t = item.get("tags", [])
        if isinstance(t, list):
            tags.extend([x for x in t if ":" not in x and x not in ("safetensors", "endpoints_compatible", "transformers", "region:us")])
            
    counter = Counter(tags)
    top_5 = counter.most_common(5)
    
    if not top_5:
        top_5 = [("No Tags Found", 1)]
        
    total_tags = sum(count for _, count in top_5)
    colors = ["#3178c6", "#00b4ab", "#e34c26", "#4f5b93", "#178600"]
    
    bars = ""
    y_offset = 65
    
    for i, (tag, count) in enumerate(top_5):
        perc = (count / total_tags) * 100
        color = colors[i % len(colors)]
        
        bars += f'''
    <g transform="translate(25, {y_offset})">
      <circle cx="5" cy="-4" r="4" fill="{color}" />
      <text x="15" y="0" class="tag-name">{tag} ({perc:.1f}%)</text>
    </g>'''
        y_offset += 25

    return f"""<svg width="300" height="195" viewBox="0 0 300 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #aaaaaa; }}
    .tag-name {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
  </style>
  <rect x="0.5" y="0.5" rx="20" width="294" height="194" fill="#0d1117" stroke="#e4e2e2" stroke-opacity="0" />
  <text x="25" y="35" class="header">Top ML Tags</text>
  {bars}
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
