import json
import time
import urllib.error
import urllib.request


def get_json(url: str, timeout: float = 10.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode())


def wait_for_health(base_url: str, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"scoring-service did not become healthy within {timeout_s}s: {last_error}")
