name: Update HF Activity

on:
  schedule:
    # Jalan tiap 30 menit. Ubah "*/30" sesuai kebutuhan (jangan terlalu sering,
    # GitHub Actions cron minimum realistis ~5 menit dan sering telat sedikit).
    - cron: "*/30 * * * *"
  workflow_dispatch: {}   # tombol "Run workflow" manual di tab Actions

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install requests

      - name: Scrape status HF & update README
        id: scrape
        env:
          HF_USERNAME: maftuh-main
        run: |
          python scripts/update_hf_status.py
        continue-on-error: true

      - name: Commit & push jika ada perubahan
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          git diff --cached --quiet || git commit -m "chore: update HF activity [skip ci]"
          git push
