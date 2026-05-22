class PaymentClient:
    def authorize(self, payload):
        response = self.gateway.post("/authorize", json=payload, timeout=3)
        if response.status_code == 504:
            raise PaymentTimeout("upstream gateway timed out")
        return response.json()
