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
            content_length = headers.get("content-length") or headers.get("Content-Length")
            if content_length:
                self.inbound_bytes += int(content_length)
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
        bytes_per_kb = 1024

        inbound_total_bytes = self.inbound_bytes
        outbound_total_bytes = self.outbound_bytes
        total_bytes = inbound_total_bytes + outbound_total_bytes

        def as_units(value_bytes: int) -> dict:
            return {
                "bytes": value_bytes,
                "kilobytes": round(value_bytes / bytes_per_kb, 2),
                "megabytes": round(value_bytes / BYTES_PER_MB, 2),
                "gigabytes": round(value_bytes / BYTES_PER_GB, 4),
            }

        return {
            "inbound": as_units(inbound_total_bytes),
            "outbound": as_units(outbound_total_bytes),
            "total": as_units(total_bytes),
        }
