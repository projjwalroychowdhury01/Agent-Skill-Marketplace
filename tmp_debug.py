from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
resp = client.get('/skills/search', params={'query': 'json extraction', 'page': 1, 'size': 5})
print(resp.status_code)
print(resp.text)
