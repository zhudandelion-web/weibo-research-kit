# Contributing / 参与贡献

Thanks for helping maintain a free research tool. Report reproducible bugs and concrete research tasks through GitHub Issues. Include your OS, Python version, command/tool name, expected behavior and redacted status output. Never submit account cookies, API keys, login codes or databases.

For code changes, install the project into a virtual environment and run `python -m unittest discover -s tests -v`. Offline tests must not contact Weibo. Keep guest-only access, source attribution, decimal-string IDs, ambiguous empty-result semantics and historical snapshots intact. Add regression tests for actual fixes.

Network checks are opt-in: `weibo-research doctor --live` reads two current hot topics. A blocked visitor endpoint can be an external access limitation; it is not sufficient evidence that there are no posts.

Small, focused pull requests are easiest to maintain. Explain the problem and include verification. Broad features and dependency upgrades require compatibility checks; no guaranteed support SLA is offered. Do not remove upstream attribution or commit runtime data.
