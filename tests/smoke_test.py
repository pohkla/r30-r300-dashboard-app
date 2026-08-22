import os
import re
import shutil
import sys
import tempfile
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["COOKIE_SECURE"] = "false"
os.environ["ADMIN_PASSWORD"] = "test-password"

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from main import app, normalize_trade, store  # noqa: E402


def run() -> None:
    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "R30 / R300 Dashboard" in response.text
    assert "อัปเดตถึงแผน #11" in response.text
    assert client.get("/admin", follow_redirects=False).status_code == 303

    login_page = client.get("/login")
    csrf = re.search(r'name="csrf" value="([^"]+)"', login_page.text).group(1)
    response = client.post("/login", data={"csrf": csrf, "password": "test-password"}, follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/admin"
    assert client.get("/admin").status_code == 200

    plans = [normalize_trade(item) for item in store.load(force=True)]
    assert len(plans) == 11
    assert sum(item["result"] for item in plans) == 12500
    assert next(item for item in plans if item["id"] == 10)["result"] == 2500

    with tempfile.TemporaryDirectory() as temp_dir:
        test_data = Path(temp_dir) / "trades.json"
        shutil.copy(ROOT / "data" / "trades.json", test_data)
        main.LOCAL_DATA = test_data
        store.cache = None
        form_page = client.get("/admin/trade/new")
        form_csrf = re.search(r'name="csrf" value="([^"]+)"', form_page.text).group(1)
        saved = client.post(
            "/admin/trade/save",
            data={
                "csrf": form_csrf, "id": "0", "side": "BUY", "status": "pending",
                "entry": "4500", "stop_loss": "4470", "tp1": "4560", "tp2": "",
                "highest_target": "", "open_at": "2026-08-21T16:00", "close_at": "", "note": "smoke test",
            },
            follow_redirects=False,
        )
        assert saved.status_code == 303
        assert len(json.loads(test_data.read_text(encoding="utf-8"))) == 12

    print("SMOKE_TEST_OK plans=11 net=12500 auth=PASS write=PASS")


if __name__ == "__main__":
    run()
