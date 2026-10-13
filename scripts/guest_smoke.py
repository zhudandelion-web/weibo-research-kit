"""Opt-in two-row visitor check; artifact contains status metadata, not post content."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from weibo_research.core import Config, Service

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        result = await Service(Config(Path(tmp),archive=False)).query("get_trendings","maintenance:trending",limit=2)
    report = {k:result[k] for k in ("status","count","collected_at","access_mode","error_type","http_trace")}
    Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False))
    if report["status"] not in ("public_sample","partial") or report["count"] == 0:
        raise SystemExit(2)

asyncio.run(main())
