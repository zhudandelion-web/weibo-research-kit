# English quick start

Weibo Research Kit is an alpha research layer on top of `mcp-server-weibo`. It does not require a personal Weibo login, API key or account cookie. It uses public guest sessions, which Weibo may restrict at any time.

Install Python 3.11+, extract the source archive, and run from its directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/weibo-research doctor
.venv/bin/weibo-research collect --keyword "人工智能" --limit 5
```

On Windows use `py -3 -m venv .venv`, `.venv\Scripts\python.exe` and `.venv\Scripts\weibo-research.exe`. Configure your stdio MCP client with the absolute path to `weibo-research` and the argument `serve`. See `examples/mcp.json`. This package has not been published to PyPI.

The seven tools cover content search, user search, profiles, account feed samples, trends, comments and local archive search. IDs are decimal strings. All network calls return a collection timestamp, run ID, completeness flags, and a bounded status trace. Post snapshots survive later re-collection; use `search-saved --run-id ID` to inspect the earlier sample. `export --run-id ID` exports it with its query and collection status.

`--profile NAME` separates local archives but does not authenticate customers. `--no-archive` disables saving new network results. Default storage is the OS user-data directory, overridable with `--data-dir` or `WEIBO_RESEARCH_DATA_DIR`. Queries and post content may be sensitive; the AI client receives whatever its tools request. Stop the server before deleting your local profile database.

JSONL retains exact text and decimal-string IDs. CSV prepends an apostrophe to identifiers and potentially executable formulas. No export overwrites an existing file.

Samples are not complete histories, full-text guarantees, newest rankings, or representative sentiment surveys. `empty_unconfirmed` never proves absence. Rate limiting or platform changes may stop a query. See the Chinese README for status semantics and `CHATGPT.md` for optional cloud-account integration.
