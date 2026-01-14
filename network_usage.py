from typing import Optional
from playwright.async_api import Page, Request, Response

BYTES_PER_GB = 1024 * 1024 * 1024
BYTES_PER_MB = 1024 * 1024


class NetworkUsage:
    inbound_bytes: int
    outbound_bytes: int

    def __init__(self) -> None:
        self.inbound_bytes = 0
        self.outbound_bytes = 0

    def add_inbound_from_response(self, resp: Response) -> None:
        # Prefer Content-Length; chunked responses may not have it.
        try:
            headers = resp.headers or {}
            clen = headers.get("content-length") or headers.get("Content-Length")
            if clen:
                self.inbound_bytes += int(clen)
        except Exception:
            # Best-effort; ignore if header missing or malformed.
            pass

    def add_outbound_from_request(self, req: Request) -> None:
        try:
            data = req.post_data or ""
            # post_data is a string; approximate UTF-8 byte size.
            self.outbound_bytes += len(data.encode("utf-8"))
        except Exception:
            pass

    def attach(self, page: Page) -> None:
        page.on("response", lambda r: self.add_inbound_from_response(r))
        page.on("request", lambda q: self.add_outbound_from_request(q))

    def snapshot(self) -> dict:
        return {
            "inbound_bytes": self.inbound_bytes,
            "outbound_bytes": self.outbound_bytes,
            "inbound_mb": round(self.inbound_bytes / BYTES_PER_MB, 2),
            "outbound_mb": round(self.outbound_bytes / BYTES_PER_MB, 2),
            "inbound_gb": round(self.inbound_bytes / BYTES_PER_GB, 4),
            "outbound_gb": round(self.outbound_bytes / BYTES_PER_GB, 4),
            "total_gb": round(
                (self.inbound_bytes + self.outbound_bytes) / BYTES_PER_GB, 4
            ),
        }
