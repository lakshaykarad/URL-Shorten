from fastapi.testclient import TestClient
from main import app

def test_system_status():
    with TestClient(app) as client:
        response = client.get("/") 
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "System Online"
        assert data["postgres"] in ["Connected", "Connecting"]
        assert data["redis"] in ["Connected", "Connecting"]
        
def test_redis_system():
    with TestClient(app) as client:
        for i in range(6):
            response = client.post("/shorten", json={"url": "https://test.com"})
        
        response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        