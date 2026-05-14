import sys
import os
import json

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from app.models.user import User

client = TestClient(app)
db = SessionLocal()

results = {}

# 1. Cadastro
payload = {
  "name": "Teste Usuario",
  "email": "teste@example.com",
  "password": "SenhaForte123"
}
response1 = client.post("/auth/register", json=payload)
results["1_register"] = {"status": response1.status_code, "json": response1.json()}

# 2. Cadastro duplicado
response2 = client.post("/auth/register", json=payload)
results["2_register_dup"] = {"status": response2.status_code, "json": response2.json()}

# 3. Login
login_payload = {"username": "teste@example.com", "password": "SenhaForte123"}
response3 = client.post("/auth/login", data=login_payload)
results["3_login"] = {"status": response3.status_code, "json": response3.json()}

# 4. Login senha errada
login_wrong = {"username": "teste@example.com", "password": "SenhaErrada"}
response4 = client.post("/auth/login", data=login_wrong)
results["4_login_wrong"] = {"status": response4.status_code, "json": response4.json()}

# 5. Rota protegida com token
token = response3.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}
response5 = client.get("/users/me", headers=headers)
results["5_me_with_token"] = {"status": response5.status_code, "json": response5.json()}

# 6. Rota protegida sem token
response6 = client.get("/users/me")
results["6_me_without_token"] = {"status": response6.status_code, "json": response6.json()}

# 7 e 8. Validação banco
user_in_db = db.query(User).filter(User.email == "teste@example.com").first()
results["7_db_user_exists"] = bool(user_in_db)
if user_in_db:
    results["8_db_password_is_hashed"] = (user_in_db.password_hash != "SenhaForte123")
    results["8_db_password_hash_value"] = user_in_db.password_hash[:15] + "..."
else:
    results["8_db_password_is_hashed"] = False

# Cleanup
if user_in_db:
    db.delete(user_in_db)
    db.commit()

db.close()

print(json.dumps(results, indent=2))
