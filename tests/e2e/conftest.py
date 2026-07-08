import os
import subprocess
import sys
from pathlib import Path

import pytest

from http_helpers import wait_for_health

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_DIR = REPO_ROOT / "packages" / "synthetic-data-generator"
SCORING_SERVICE_DIR = REPO_ROOT / "services" / "scoring-service"
SMOKE_PORT = 8099
PER_ARCHETYPE = 5


@pytest.fixture(scope="session")
def smoke_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Runs the real generator CLI as a subprocess (not an import) — this
    is the actual command a demo/deploy would run, so the smoke test
    exercises the real contract between the two packages, not an
    approximation of it.
    """
    data_dir = tmp_path_factory.mktemp("e2e-smoke-data")
    subprocess.run(
        [
            sys.executable,
            str(GENERATOR_DIR / "cli.py"),
            "--per-archetype",
            str(PER_ARCHETYPE),
            "--seed",
            "e2e-smoke",
            "--output-dir",
            str(data_dir),
        ],
        check=True,
    )
    return data_dir


@pytest.fixture(scope="session")
def smoke_backend_url(smoke_data_dir: Path):
    """Launches the real scoring-service (uvicorn subprocess, not an
    in-process TestClient) pointed at the generated data, so this is a true
    end-to-end smoke test of what a deployed instance would actually do.
    """
    env = {**os.environ, "SYNTHETIC_DATA_DIR": str(smoke_data_dir)}
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(SMOKE_PORT)],
        cwd=str(SCORING_SERVICE_DIR),
        env=env,
        # Discard, don't pipe: an unread PIPE fills its OS buffer once uvicorn
        # logs enough access-log lines, and the child process then blocks on
        # write() — every request silently hangs. Discarding avoids that
        # deadlock entirely since nothing here needs the subprocess's output.
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{SMOKE_PORT}"
    try:
        wait_for_health(base_url)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
