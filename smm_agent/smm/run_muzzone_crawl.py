"""Run the Muzzone listing crawl and write derived JSON (no raw HTML kept)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from smm.muzzone_crawl import BASE, crawl_listing

PATHS = {
    "sale": "/rasprodazha.html",
    "digital_pianos": "/cifrovye-fortepiano/",
    "ukulele": "/ukulele/",
    "kids": "/detskie/",
    "acoustic_guitars": "/akusticheskie/",
    "electric_guitars": "/elektrogitari/",
}

def main(out: Path) -> None:
    data = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": BASE, "lists": {}}
    for key, path in PATHS.items():
        try:
            items = crawl_listing(path)
        except Exception as e:  # keep going; record why a list is missing
            data["lists"][key] = {"path": path, "n": 0, "items": [], "error": repr(e)}
            print(f"{key:18s} ERROR {e!r}", file=sys.stderr)
            continue
        data["lists"][key] = {"path": path, "n": len(items), "items": items}
        print(f"{key:18s} {len(items):4d} items", file=sys.stderr)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main(Path(sys.argv[1]))
