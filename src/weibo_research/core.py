from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx
from platformdirs import user_data_path
from mcp_server_weibo.weibo import WeiboCrawler


@dataclass(frozen=True)
class Config:
    data_dir: Path
    archive: bool = True
    request_interval: float = 1.5
    timeout: float = 60

    @classmethod
    def load(cls, data_dir=None, profile="default", archive=True):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile):
            raise ValueError("Profile must contain 1–64 letters, digits, underscores or hyphens")
        base = Path(data_dir or os.environ.get("WEIBO_RESEARCH_DATA_DIR") or user_data_path("weibo-research-kit", appauthor=False))
        return cls(base.expanduser().resolve() / profile, archive)

    def __post_init__(self):
        if self.request_interval < 1 or not 5 <= self.timeout <= 120:
            raise ValueError("Request interval must be >=1 second; timeout must be 5–120 seconds")


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p"):
            self.parts.append("\n")


def normalize(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, list):
        return [normalize(x) for x in value]
    if isinstance(value, dict):
        return {k: str(v) if k in ("id", "uid", "feed_id") and isinstance(v, int) else normalize(v) for k, v in value.items()}
    return value


def enrich(post):
    item = dict(normalize(post))
    parser = PlainText()
    parser.feed(item.get("text", ""))
    item["plain_text"] = "".join(parser.parts).strip()
    item["source_url"] = f'https://m.weibo.cn/detail/{item["id"]}'
    item["text_completeness"] = "possibly_truncated" if "全文" in item["plain_text"] or re.search(r"(?:\.{2,}|…+)\s*$", item["plain_text"]) else "unverified"
    return item


def classify(data, trace, error):
    failed = error is not None or any(x.get("failed", False) for x in trace)
    return "partial" if data and failed else "error" if failed else "public_sample" if data else "empty_unconfirmed"


class RequestGate:
    def __init__(self, interval):
        self.interval = interval
        self.last = None
        self.lock = asyncio.Lock()
        self.clock = time.monotonic
        self.sleep = asyncio.sleep

    async def __call__(self, request):
        async with self.lock:
            if self.last is not None:
                await self.sleep(max(0, self.interval - (self.clock() - self.last)))
            self.last = self.clock()


class GuestCrawler(WeiboCrawler):
    """Uses only in-memory guest cookies. Never loads or saves account sessions."""
    def __init__(self, config):
        super().__init__(load_persisted_session=False)
        self.trace = []
        self.gate = RequestGate(config.request_interval)
        self.logger = logging.getLogger("weibo_research.upstream")
        self.logger.setLevel(logging.CRITICAL)

    def _load_cookies(self):
        raise RuntimeError("Account cookies are not supported")

    def _save_cookies(self, cookies):
        raise RuntimeError("Account cookies are not supported")

    def _create_client(self, **kwargs):
        client = super()._create_client(**kwargs)
        client.timeout = httpx.Timeout(15)
        client.event_hooks = {"request": [self.gate], "response": [self.record]}
        return client

    async def record(self, response):
        await response.aread()
        row = {"host": response.request.url.host, "path": response.request.url.path, "http_status": response.status_code, "failed": response.status_code >= 400}
        try:
            body = response.json()
            if isinstance(body, dict) and "ok" in body:
                row["ok"] = body["ok"]
                row["failed"] = row["failed"] or body["ok"] not in (1, True)
        except ValueError:
            if response.request.url.host == "m.weibo.cn" and response.request.url.path.startswith("/api/"):
                row["failed"] = True
                row["unexpected_response"] = True
        # Never save request query strings, headers, cookies or response messages.
        self.trace.append(row)


class Archive:
    def __init__(self, config):
        self.path = config.data_dir / "archive.sqlite3"

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.is_symlink():
            raise ValueError("Archive database must not be a symbolic link")
        conn = sqlite3.connect(self.path, timeout=10)
        if os.name != "nt":
            self.path.chmod(0o600)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript('''
          CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY, method TEXT, query TEXT, collected_at TEXT,
            status TEXT, returned_count INTEGER, trace_json TEXT);
          CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY, author_id TEXT, author_name TEXT,
            text TEXT, source_url TEXT, text_completeness TEXT,
            published_at_raw TEXT, collected_at TEXT, last_run_id TEXT);
          CREATE TABLE IF NOT EXISTS samples (
            run_id TEXT REFERENCES runs(run_id), post_id TEXT REFERENCES posts(post_id),
            raw_json TEXT, PRIMARY KEY(run_id,post_id));
          CREATE INDEX IF NOT EXISTS posts_author ON posts(author_id);
        ''')
        return conn

    def save(self, result):
        posts = result["data"] if result["method"] in ("search_content", "get_feeds") else []
        conn = self.connect()
        try:
            with conn:
                conn.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?)", (result["run_id"],result["method"],result["query"],result["collected_at"],result["status"],result["count"],json.dumps(result["http_trace"])))
                for post in posts:
                    user = post.get("user") or {}
                    conn.execute('''INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(post_id) DO UPDATE SET
                      author_id=excluded.author_id,author_name=excluded.author_name,text=excluded.text,
                      source_url=excluded.source_url,text_completeness=excluded.text_completeness,
                      published_at_raw=excluded.published_at_raw,collected_at=excluded.collected_at,last_run_id=excluded.last_run_id''',
                      (str(post["id"]),str(user.get("id","")),user.get("screen_name",""),post["plain_text"],post["source_url"],post["text_completeness"],post.get("created_at",""),result["collected_at"],result["run_id"]))
                    conn.execute("INSERT OR REPLACE INTO samples VALUES (?,?,?)", (result["run_id"],str(post["id"]),json.dumps(post,ensure_ascii=False)))
        finally:
            conn.close()

    def search(self, keyword="", uid=None, limit=50, offset=0, run_id=None):
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("Local limit must be 1–100 and offset must be nonnegative")
        conn = self.connect()
        try:
            if run_id:
                rows = conn.execute('''SELECT s.raw_json,r.collected_at,r.query,r.status FROM samples s JOIN runs r USING(run_id)
                    WHERE s.run_id=? ORDER BY s.post_id''', (run_id,)).fetchall()
                data = [dict(json.loads(r["raw_json"]),collected_at=r["collected_at"],collection_query=r["query"],collection_status=r["status"],run_id=run_id) for r in rows]
                data = [x for x in data if keyword in x["plain_text"] and (uid is None or str((x.get("user") or {}).get("id")) == str(uid))]
                return data[offset:offset+limit]
            rows = conn.execute('''SELECT p.*,r.query AS collection_query,r.status AS collection_status FROM posts p JOIN runs r ON p.last_run_id=r.run_id
                WHERE instr(p.text,?)>0 AND (? IS NULL OR p.author_id=?)
                ORDER BY p.collected_at DESC,p.post_id LIMIT ? OFFSET ?''', (keyword,uid,uid,limit,offset)).fetchall()
            return [dict(x) for x in rows]
        finally:
            conn.close()

    def stats(self):
        conn = self.connect()
        try:
            return {t:conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("posts","runs","samples")}
        finally:
            conn.close()

    def export(self, path, format="jsonl", run_id=None):
        conn = self.connect()
        try:
            if run_id:
                rows = conn.execute('''SELECT s.raw_json,r.collected_at,r.query,r.status FROM samples s JOIN runs r USING(run_id) WHERE s.run_id=? ORDER BY s.post_id''',(run_id,)).fetchall()
                data = [dict(json.loads(r["raw_json"]),run_id=run_id,collected_at=r["collected_at"],collection_query=r["query"],collection_status=r["status"]) for r in rows]
            else:
                data = [dict(r) for r in conn.execute('''SELECT p.*,r.query AS collection_query,r.status AS collection_status FROM posts p JOIN runs r ON p.last_run_id=r.run_id ORDER BY p.collected_at,p.post_id''')]
        finally:
            conn.close()
        if format not in ("jsonl", "csv"):
            raise ValueError("Export format must be jsonl or csv")
        # Create exclusively: never overwrite an existing user file.
        with Path(path).open("x",encoding="utf-8",newline="") as f:
            if os.name != "nt":
                os.fchmod(f.fileno(),0o600)
            if format == "jsonl":
                for row in data:
                    f.write(json.dumps(row,ensure_ascii=False)+"\n")
            else:
                fields = ["post_id","author_id","author_name","text","source_url","text_completeness","published_at_raw","collected_at","run_id","collection_query","collection_status"]
                writer = csv.DictWriter(f,fields)
                writer.writeheader()
                for row in data:
                    if "user" in row:
                        row = dict(row,post_id=row["id"],author_id=(row.get("user") or {}).get("id",""),author_name=(row.get("user") or {}).get("screen_name",""),text=row["plain_text"],published_at_raw=row.get("created_at",""))
                    row = dict(row,run_id=row.get("run_id",row.get("last_run_id","")))
                    writer.writerow({k: csv_safe(row.get(k,""),identifier=k in ("post_id","author_id")) for k in fields})
        return len(data)


def csv_safe(value, identifier=False):
    s = str(value or "")
    if s and (identifier or s.lstrip().startswith(("=","+","-","@","\t","\r","\n")) or s.startswith(("\t","\r","\n"))):
        return "'" + s
    return s


class Service:
    def __init__(self, config, crawler=None):
        self.config = config
        self.crawler = crawler or GuestCrawler(config)
        self.archive = Archive(config)
        self.lock = asyncio.Lock()

    async def query(self, method, query, **kwargs):
        async with self.lock:
            self.crawler.trace.clear()
            collected = datetime.now(timezone.utc).isoformat()
            error = None
            data = []
            try:
                async with asyncio.timeout(self.config.timeout):
                    await self.crawler._ensure_cookies()
                    raw = normalize(await getattr(self.crawler,method)(**kwargs))
                    data = raw if isinstance(raw,list) else [raw] if raw else []
                    if method in ("search_content","get_feeds"):
                        data = [enrich(x) for x in data]
            except Exception as exc:
                error = type(exc).__name__
            trace = list(self.crawler.trace)
            result = {"run_id":uuid.uuid4().hex,"method":method,"query":query,"status":classify(data,trace,error),"count":len(data),"data":data,"collected_at":collected,"access_mode":"guest-only","full_history_verified":False,"full_text_verified":False,"error_type":error,"http_trace":trace,"archive_status":"disabled"}
            if self.config.archive:
                try:
                    self.archive.save(result)
                    result["archive_status"] = "saved"
                except Exception as exc:
                    result["archive_status"] = "error"
                    result["archive_error_type"] = type(exc).__name__
            return result
