import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app
import datetime

client = TestClient(app)

@patch("src.presentation.api.auth.es_usuario_permitido")
def test_request_otp_con_chat_id_no_autorizado_retorna_403(mock_es_usuario_permitido):
    mock_es_usuario_permitido.return_value = False
    response = client.post("/api/auth/request-otp", json={"chat_id": "99999"})
    assert response.status_code == 403

def test_verify_otp_con_codigo_invalido_retorna_400():
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    
    mock_db = {
        "test_chat": {
            "code": "1234",
            "expires_at": future_time
        }
    }
    
    with patch("src.presentation.api.auth.es_usuario_permitido", return_value=True):
        with patch.dict("src.presentation.api.auth.otp_store", mock_db, clear=True):
            response = client.post("/api/auth/verify-otp", json={"chat_id": "test_chat", "code": "9999"})
            assert response.status_code == 400
