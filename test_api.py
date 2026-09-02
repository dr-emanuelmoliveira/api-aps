import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

class TestAPI:
    """Testes da API principal"""
    
    def test_health_check(self):
        """Testa se a API está respondendo"""
        response = client.get("/")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_docs_available(self):
        """Testa se a documentação Swagger está disponível"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_available(self):
        """Testa se ReDoc está disponível"""
        response = client.get("/redoc")
        assert response.status_code == 200

class TestMessages:
    """Testes de envio de mensagens"""
    
    def test_missing_api_key(self):
        """Testa erro quando falta API key"""
        response = client.post(
            "/message/sendText/teste",
            json={"number": "5537984198778", "textMessage": {"text": "Test"}}
        )
        # Deve retornar erro de autenticação
        assert response.status_code in [401, 403]
    
    def test_invalid_number_format(self):
        """Testa erro com número inválido"""
        response = client.post(
            "/message/sendText/teste",
            json={"number": "123", "textMessage": {"text": "Test"}},
            headers={"apikey": "test-key"}
        )
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
