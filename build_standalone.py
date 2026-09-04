from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "mushaf-v2.css").read_text(encoding="utf-8")
    app = (ROOT / "mushaf-v2.js").read_text(encoding="utf-8")
    questions = (ROOT / "questions.js").read_text(encoding="utf-8")
    font = base64.b64encode((ROOT / "amiri-quran.ttf").read_bytes()).decode("ascii")
    icon = base64.b64encode((ROOT / "icons" / "icon-192.png").read_bytes()).decode("ascii")
    css = css.replace("url('amiri-quran.ttf')", f"url('data:font/ttf;base64,{font}')")
    page = page.replace('<link rel="manifest" href="manifest.webmanifest">', '')
    page = page.replace('icons/icon-192.png', f'data:image/png;base64,{icon}')
    page = page.replace('<link rel="stylesheet" href="mushaf-v2.css">', f"<style>{css}</style>")
    page = page.replace('<script src="questions.js"></script><script src="mushaf-v2.js"></script>', f"<script>{questions}</script><script>{app}</script>")
    page = page.replace("if('serviceWorker'in navigator&&location.protocol.startsWith('http'))navigator.serviceWorker.register('service-worker.js').catch(()=>{});", "")
    output = ROOT.parent.parent / "basair_mushaf_complete_v5_4.html"
    output.write_text(page, encoding="utf-8")
    print(f"built={output} bytes={output.stat().st_size}")


if __name__ == "__main__":
    main()
