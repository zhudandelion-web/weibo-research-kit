import argparse
import asyncio
import json
import sys
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

from . import __version__
from .core import Archive, Config, Service


def identifier(value):
    if not value.isdecimal() or not value.isascii() or not 1 <= len(value) <= 20 or int(value) <= 0:
        raise argparse.ArgumentTypeError("ID must be 1–20 ASCII decimal digits and positive")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Guest-only Weibo research tools and a private local evidence archive")
    parser.add_argument("--version",action="version",version=__version__)
    parser.add_argument("--data-dir",help="Local archive base directory; otherwise uses WEIBO_RESEARCH_DATA_DIR or OS user-data directory")
    parser.add_argument("--profile",default="default",help="Separate archive namespace, not an authentication boundary")
    parser.add_argument("--no-archive",action="store_true",help="Do not save new network query results or traces")
    parser.add_argument("--request-interval",type=float,default=1.5,help="Minimum seconds between HTTP requests (>=1)")
    sub = parser.add_subparsers(dest="command",required=True)
    sub.add_parser("serve",help="Run the seven read-only MCP tools over stdio")
    doctor = sub.add_parser("doctor",help="Check installed dependencies and local archive; no network unless --live")
    doctor.add_argument("--live",action="store_true")
    collect = sub.add_parser("collect",help="Collect a small public post sample")
    target = collect.add_mutually_exclusive_group(required=True)
    target.add_argument("--keyword")
    target.add_argument("--uid",type=identifier)
    collect.add_argument("--limit",type=int,default=10,choices=range(1,31))
    collect.add_argument("--page",type=int,default=1,choices=range(1,6))
    search = sub.add_parser("search-saved")
    search.add_argument("keyword")
    search.add_argument("--uid",type=identifier)
    search.add_argument("--run-id")
    search.add_argument("--limit",type=int,default=50,choices=range(1,101))
    search.add_argument("--offset",type=int,default=0)
    sub.add_parser("stats")
    export = sub.add_parser("export")
    export.add_argument("path",type=Path)
    export.add_argument("--format",choices=("jsonl","csv"),default="jsonl")
    export.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        config = replace(Config.load(args.data_dir,args.profile,not args.no_archive),request_interval=args.request_interval)
        if args.command == "serve":
            from .server import create_server
            create_server(config).run(transport="stdio")
            return
        archive = Archive(config)
        if args.command == "collect":
            if args.keyword is not None and (not args.keyword.strip() or len(args.keyword)>200):
                raise ValueError("Keyword must contain 1–200 characters")
            service = Service(config)
            if args.keyword is not None:
                data = asyncio.run(service.query("search_content",f"keyword:{args.keyword}",keyword=args.keyword,limit=args.limit,page=args.page))
            else:
                data = asyncio.run(service.query("get_feeds",f"uid:{args.uid}",uid=int(args.uid),limit=args.limit))
        elif args.command == "search-saved":
            rows = archive.search(args.keyword,args.uid,args.limit,args.offset,args.run_id)
            data = {"status":"local_archive_results","live_search":False,"count":len(rows),"data":rows}
        elif args.command == "stats":
            data = archive.stats()
        elif args.command == "export":
            data = {"exported_posts":archive.export(args.path,args.format,args.run_id),"format":args.format}
        else:
            data = {"version":__version__,"python":sys.version.split()[0],"dependencies":{name:version(name) for name in ("mcp-server-weibo","fastmcp")},"guest_only":True,"archive_enabled":config.archive,"archive_path":str(archive.path),"local_stats":archive.stats()}
            if args.live:
                result = asyncio.run(Service(config).query("get_trendings","doctor:trending",limit=2))
                data["live_check"] = {k:v for k,v in result.items() if k != "data"}
                if result["status"] not in ("public_sample","partial"):
                    print(json.dumps(data,ensure_ascii=False,indent=2))
                    raise SystemExit(2)
        print(json.dumps(data,ensure_ascii=False,indent=2))
        if args.command == "collect" and data["status"] == "error":
            raise SystemExit(2)
    except (OSError,ValueError) as exc:
        # Do not echo exception messages containing paths, content or credentials.
        print(json.dumps({"status":"local_error","error_type":type(exc).__name__}),file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
