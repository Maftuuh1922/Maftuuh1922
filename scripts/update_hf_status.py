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


def build_spaces_table(spaces: list[dict]) -> str:
    if not spaces:
        return "_Belum ada Space yang terdeteksi._"

    rows = [
        "| Space | Status | Likes | SDK |",
        "|:------|:-------|:-----:|:----|",
    ]
    for s in spaces:
        stage = s.get("runtime", {}).get("stage", "UNKNOWN")
        status_label = STAGE_EMOJI.get(stage, f"⚪ {stage}")
        name = s.get("id", "").split("/")[-1]
        url = f"https://huggingface.co/spaces/{s.get('id')}"
        likes = s.get("likes", 0)
        sdk = s.get("sdk", "-")
        rows.append(f"| [{name}]({url}) | {status_label} | {likes} | `{sdk}` |")
    return "\n".join(rows)


def build_models_table(models: list[dict]) -> str:
    if not models:
        return "_Belum ada Model yang terdeteksi._"

    rows = [
        "| Model | Downloads | Likes |",
        "|:------|:---------:|:-----:|",
    ]
    for m in models:
        name = m.get("id", "").split("/")[-1]
        url = f"https://huggingface.co/{m.get('id')}"
        downloads = m.get("downloads", 0)
        likes = m.get("likes", 0)
        rows.append(f"| [{name}]({url}) | {downloads} | {likes} |")
    return "\n".join(rows)


def build_block(username: str) -> str:
    spaces = fetch_spaces(username)
    models = fetch_models(username)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    block = [
        START_MARKER,
        f"<sub>🔄 Terakhir diperbarui otomatis: {now}</sub>",
        "",
        "**🚀 Spaces**",
        "",
        build_spaces_table(spaces),
        "",
        "**🧠 Models**",
        "",
        build_models_table(models),
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
