import json
import urllib.error
import urllib.request
from pathlib import Path

path = Path.home() / ".gemini/antigravity-cli/antigravity-oauth-token"
token = json.loads(path.read_text())["token"]["access_token"]
if not isinstance(token, str) or not token:
    raise SystemExit("OAuth access token missing")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": "http://127.0.0.1:18047"}))
request = urllib.request.Request(
    "https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
    data=json.dumps({"metadata": {"ideType": 9, "platform": 3, "pluginType": 2}}).encode(),
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
)
try:
    with opener.open(request, timeout=25) as response:
        data = json.load(response)
        print("Google HTTP:", response.status)
        print("Response fields:", ", ".join(sorted(data)))
        print("Current tier:", data.get("currentTier", {}).get("id"))
        print("Ineligible tiers:", json.dumps(data.get("ineligibleTiers", []), ensure_ascii=False))
except urllib.error.HTTPError as error:
    print("Google HTTP:", error.code)
    try:
        detail = json.load(error).get("error", {})
        print("Google error:", detail.get("status"), detail.get("message"))
    except (ValueError, AttributeError):
        print("Non-JSON error response")
    raise SystemExit(1)
except (OSError, urllib.error.URLError) as error:
    print("Connection failed:", type(error).__name__)
    raise SystemExit(1)
