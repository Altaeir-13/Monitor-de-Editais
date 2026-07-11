import json
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)
results = {}

health_response = client.get("/health")
results["1_health_status"] = health_response.status_code == 200
results["2_health_body"] = health_response.json() == {"status": "ok"}

ready_response = client.get("/ready")
results["3_ready_status"] = ready_response.status_code == 200
results["4_ready_body"] = ready_response.json() == {"status": "ok"}

openapi_response = client.get("/openapi.json")
results["5_openapi_status"] = openapi_response.status_code == 200
results["6_health_documented"] = "/health" in openapi_response.json().get("paths", {})
results["7_ready_documented"] = "/ready" in openapi_response.json().get("paths", {})

print(json.dumps(results, indent=2))
assert all(results.values()), results
