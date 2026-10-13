import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

import httpx

from weibo_research.core import Archive, Config, GuestCrawler, RequestGate, Service, classify, csv_safe, enrich, normalize


def result(run_id, text, query="keyword:测试"):
    return {"run_id":run_id,"method":"search_content","query":query,"collected_at":"2026-10-13T01:00:00+00:00","status":"public_sample","count":1,"http_trace":[],"data":[enrich({"id":5352926253944902,"text":text,"user":{"id":123,"screen_name":"示例"}})]}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Config.load(self.tmp.name)
        self.archive = Archive(self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def test_repeated_posts_keep_original_run_evidence(self):
        self.archive.save(result("first","第一次正文"))
        self.archive.save(result("second","修改后正文","keyword:第二次"))
        self.assertEqual(self.archive.stats(),{"posts":1,"runs":2,"samples":2})
        self.assertEqual(self.archive.search("正文")[0]["text"],"修改后正文")
        self.assertEqual(self.archive.search("正文",run_id="first")[0]["plain_text"],"第一次正文")
        self.assertEqual(self.archive.search("正文",uid="999"),[])

    def test_wildcards_are_literal_and_ids_are_preserved(self):
        self.archive.save(result("a","含100% 和下划线_"))
        self.assertEqual(len(self.archive.search("100%")),1)
        self.assertEqual(self.archive.search("%' OR 1=1 --"),[])
        self.assertEqual(self.archive.search("_")[0]["post_id"],"5352926253944902")

    def test_export_retains_snapshots_and_does_not_overwrite(self):
        self.archive.save(result("a","=IMPORTXML(恶意示例)"))
        path = Path(self.tmp.name)/"sample.csv"
        self.assertEqual(self.archive.export(path,"csv",run_id="a"),1)
        self.assertIn("'=IMPORTXML",path.read_text(encoding="utf-8"))
        self.assertIn("'5352926253944902",path.read_text(encoding="utf-8"))
        with self.assertRaises(FileExistsError):
            self.archive.export(path,"csv")
        j = Path(self.tmp.name)/"sample.jsonl"
        self.archive.export(j,run_id="a")
        self.assertEqual(json.loads(j.read_text(encoding="utf-8"))["plain_text"],"=IMPORTXML(恶意示例)")

    def test_private_files_and_profile_separation(self):
        self.archive.save(result("a","示例"))
        other = Archive(Config.load(self.tmp.name,"other"))
        self.assertEqual(other.stats()["posts"],0)
        if os.name != "nt":
            self.assertEqual(self.archive.path.stat().st_mode & 0o777,0o600)
            self.assertEqual(self.archive.path.parent.stat().st_mode & 0o777,0o700)
        with self.assertRaises(ValueError):
            Config.load(self.tmp.name,"../private")

    def test_failed_transaction_leaves_no_partial_run(self):
        broken = result("bad","示例")
        del broken["data"][0]["plain_text"]
        with self.assertRaises(KeyError):
            self.archive.save(broken)
        self.assertEqual(self.archive.stats(),{"posts":0,"runs":0,"samples":0})


class ContentTests(unittest.TestCase):
    def test_empty_and_partial_statuses(self):
        self.assertEqual(classify([],[],None),"empty_unconfirmed")
        self.assertEqual(classify([],[{"failed":True}],None),"error")
        self.assertEqual(classify([{}],[{"failed":True}],None),"partial")

    def test_long_id_html_and_truncation(self):
        item = enrich({"id":9007199254740993,"text":"甲<br>乙…全文","user":{"id":9007199254740995}})
        self.assertEqual(item["id"],"9007199254740993")
        self.assertEqual(item["user"]["id"],"9007199254740995")
        self.assertEqual(item["plain_text"],"甲\n乙…全文")
        self.assertEqual(item["text_completeness"],"possibly_truncated")
        self.assertEqual(enrich({"id":1,"text":"短文"})["text_completeness"],"unverified")

    def test_csv_injection(self):
        for s in ("=SUM(1,2)"," +1","@evil","\tvalue","\rvalue"):
            self.assertTrue(csv_safe(s).startswith("'"))
        self.assertEqual(csv_safe("正常正文"),"正常正文")


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_trace_has_no_cookie_or_query(self):
        crawler = GuestCrawler(Config(Path("unused")))
        request = httpx.Request("GET","https://m.weibo.cn/api/x?token=private",headers={"Cookie":"private"})
        response = httpx.Response(200,json={"ok":0,"msg":"private"},request=request)
        await crawler.record(response)
        self.assertTrue(crawler.trace[0]["failed"])
        self.assertNotIn("private",json.dumps(crawler.trace))
        with self.assertRaises(RuntimeError):
            crawler._load_cookies()

    async def test_html_challenge_is_error(self):
        crawler = GuestCrawler(Config(Path("unused")))
        response = httpx.Response(200,text="<html>login</html>",request=httpx.Request("GET","https://m.weibo.cn/api/x"))
        await crawler.record(response)
        self.assertTrue(crawler.trace[0]["unexpected_response"])

    async def test_archive_can_be_disabled_and_failures_are_distinct(self):
        class Fake:
            trace = []
            async def _ensure_cookies(self):
                pass
            async def search_content(self,**kw):
                return [{"id":1,"text":"样本"}]
        with tempfile.TemporaryDirectory() as tmp:
            service = Service(Config(Path(tmp)/"no-data",archive=False),Fake())
            data = await service.query("search_content","test",keyword="test")
            self.assertEqual(data["archive_status"],"disabled")
            self.assertFalse(service.archive.path.exists())
            service = Service(Config(Path(tmp)/"data"),Fake())
            with patch.object(service.archive,"save",side_effect=OSError("secret")):
                data = await service.query("search_content","test",keyword="test")
            self.assertEqual(data["status"],"public_sample")
            self.assertEqual(data["archive_error_type"],"OSError")
            self.assertNotIn("secret",json.dumps(data))

    async def test_rate_gate_waits_between_requests(self):
        gate = RequestGate(1.5)
        with patch.object(gate,"clock",side_effect=[10,10.5,11.5]), patch.object(gate,"sleep",new_callable=AsyncMock) as sleep:
            await gate(None)
            await gate(None)
        sleep.assert_awaited_once_with(1.0)


if __name__ == "__main__":
    unittest.main()
