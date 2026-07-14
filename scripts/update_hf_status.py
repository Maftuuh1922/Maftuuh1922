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


def build_block(username: str) -> str:
    spaces = fetch_spaces(username)
    models = fetch_models(username)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    total_models = len(models)
    total_spaces = len(spaces)
    total_downloads = sum(m.get("downloads", 0) for m in models)
    total_likes = sum(m.get("likes", 0) for m in models) + sum(s.get("likes", 0) for s in spaces)

    # Format badges
    badges = (
        f'<div align="center">\n'
        f'  <img src="https://img.shields.io/badge/Models-{total_models}-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Models"/>\n'
        f'  <img src="https://img.shields.io/badge/Spaces-{total_spaces}-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Spaces"/>\n'
        f'  <img src="https://img.shields.io/badge/Downloads-{total_downloads}-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Downloads"/>\n'
        f'  <img src="https://img.shields.io/badge/Likes-{total_likes}-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Likes"/>\n'
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
