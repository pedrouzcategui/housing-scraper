import os
from pathlib import Path

import pytest

import utils.logging as logging_utils


class FakePage:
    def __init__(self, url: str = "https://example.test/listing"):
        self.url = url

    async def content(self) -> str:
        return "<html><body>hi</body></html>"

    async def screenshot(self, *, path: str, full_page: bool = True) -> None:
        # Simulate Playwright writing a screenshot file.
        Path(path).write_bytes(b"PNG")


@pytest.mark.asyncio
async def test_setup_logger_creates_dir_and_log_failure_writes_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_dir = tmp_path / "snapshots"

    logging_utils.setup_logger(str(log_dir), level="INFO")
    assert log_dir.exists()

    page = FakePage()
    await logging_utils.log_failure(page, href="https://example.test/href", exc=RuntimeError("boom"))

    html_files = list(log_dir.glob("failure_*.html"))
    png_files = list(log_dir.glob("failure_*.png"))

    assert len(html_files) == 1
    assert len(png_files) == 1

    # Sanity check: HTML snapshot has content
    assert "<html" in html_files[0].read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_log_failure_with_no_page_does_not_crash(tmp_path):
    log_dir = tmp_path / "logs"
    logging_utils.setup_logger(str(log_dir), level="INFO")

    await logging_utils.log_failure(None, href=None, exc=ValueError("x"))
    assert list(log_dir.glob("failure_*.html")) == []
    assert list(log_dir.glob("failure_*.png")) == []


@pytest.mark.asyncio
async def test_log_failure_handles_snapshot_errors(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    logging_utils.setup_logger(str(log_dir), level="INFO")

    class BrokenPage(FakePage):
        async def content(self) -> str:
            raise RuntimeError("content failed")

        async def screenshot(self, *, path: str, full_page: bool = True) -> None:
            raise RuntimeError("screenshot failed")

    await logging_utils.log_failure(BrokenPage(), href="x", exc=RuntimeError("boom"))
    # Still should not create files.
    assert list(log_dir.glob("failure_*.html")) == []
    assert list(log_dir.glob("failure_*.png")) == []
