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
    return r.json()


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
    max_name = max(max_name, 25) # Minimal 25
    
    rows = [
        f"+-{'-' * max_name}-+-------------+-------+--------+",
        f"| {'Name'.ljust(max_name)} | Status      | Likes | SDK    |",
        f"+-{'-' * max_name}-+-------------+-------+--------+",
    ]
    
    for s in spaces:
        stage = s.get("runtime", {}).get("stage", "UNKNOWN")
        status_label = STAGE_EMOJI.get(stage, f"⚪ {stage}")
        name = s.get("id", "").split("/")[-1]
        likes = str(s.get("likes", 0))
        sdk = s.get("sdk", "-")
        
        # Emoji adjustment for alignment (status_label contains an emoji which might mess up monospace, 
        # but standard monospace usually treats it as 1 or 2. We'll just pad manually.
        # "⚪ UNKNOWN" is 10 chars long but visually might be 9 or 10. Let's hardcode width to 11.
        # Sebenarnya kita bisa pakai ljust biasa, di terminal monospace akan terlihat oke.
        
        rows.append(f"| {name.ljust(max_name)} | {status_label.ljust(11)} | {likes.rjust(5)} | {sdk.ljust(6)} |")
        
    rows.append(f"+-{'-' * max_name}-+-------------+-------+--------+")
    return "\n".join(rows)


def build_models_table(models: list[dict]) -> str:
    if not models:
        return "  _Belum ada Model yang terdeteksi._"

    max_name = max(len(m.get("id", "").split("/")[-1]) for m in models)
    max_name = max(max_name, 25) # Minimal 25
    
    rows = [
        f"+-{'-' * max_name}-+-----------+-------+",
        f"| {'Name'.ljust(max_name)} | Downloads | Likes |",
        f"+-{'-' * max_name}-+-----------+-------+",
    ]
    
    for m in models:
        name = m.get("id", "").split("/")[-1]
        downloads = str(m.get("downloads", 0))
        likes = str(m.get("likes", 0))
        rows.append(f"| {name.ljust(max_name)} | {downloads.rjust(9)} | {likes.rjust(5)} |")
        
    rows.append(f"+-{'-' * max_name}-+-----------+-------+")
    return "\n".join(rows)


def build_block(username: str) -> str:
    spaces = fetch_spaces(username)
    models = fetch_models(username)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    block = [
        START_MARKER,
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
