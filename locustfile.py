from locust import HttpUser, task, between

class SystemStressTest(HttpUser):   
    wait_time = between(0.1, 0.5)
     
    SHORT_CODE = "M7vmhH"

    @task(1)
    def test_health_check(self):  
        self.client.get("/")

    @task(3)
    def test_cache_hit(self):   
        self.client.get(f"/{self.SHORT_CODE}", allow_redirects=False)
