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

# Prepare users
payload_user = {"name": "Common", "email": "common@example.com", "password": "123"}
client.post("/auth/register", json=payload_user)
resp_user_login = client.post("/auth/login", data={"username": "common@example.com", "password": "123"})
token_common = resp_user_login.json().get("access_token")

admin_email = "admin@example.com"
admin_user = db.query(User).filter(User.email == admin_email).first()
if not admin_user:
    from app.services.user import create_user
    from app.schemas.user import UserCreate
    admin_user = create_user(db, UserCreate(name="Admin", email=admin_email, password="123"))
    admin_user.role = "admin"
    db.commit()

resp_admin_login = client.post("/auth/login", data={"username": admin_email, "password": "123"})
token_admin = resp_admin_login.json().get("access_token")

headers_none = {}
headers_common = {"Authorization": f"Bearer {token_common}"}
headers_admin = {"Authorization": f"Bearer {token_admin}"}

# 1. sem token retorna 401
r1 = client.get("/admin/institutions", headers=headers_none)
results["1_no_token"] = r1.status_code

# 2. usuário comum retorna 403
r2 = client.get("/admin/institutions", headers=headers_common)
results["2_common_user"] = r2.status_code

# 3. admin cria instituição
inst_payload = {"name": "Universidade de Teste", "initials": "UT", "state": "SP", "official_site_url": "http://ut.br"}
r3 = client.post("/admin/institutions", headers=headers_admin, json=inst_payload)
results["3_admin_create_inst"] = r3.status_code
inst_id = r3.json().get("id") if r3.status_code == 200 else None

# 4. admin lista instituições
r4 = client.get("/admin/institutions", headers=headers_admin)
results["4_admin_list_inst"] = r4.status_code

# 5. admin edita instituição
r5 = client.put(f"/admin/institutions/{inst_id}", headers=headers_admin, json={"name": "Universidade Editada"})
results["5_admin_edit_inst"] = r5.status_code

# 6. admin desativa instituição
r6 = client.delete(f"/admin/institutions/{inst_id}", headers=headers_admin)
results["6_admin_delete_inst"] = r6.status_code

r6_check = client.get(f"/admin/institutions/{inst_id}", headers=headers_admin)
results["6_check_soft_delete"] = r6_check.json().get("is_active") == False

# 7. admin cria fonte vinculada
source_payload = {
    "institution_id": inst_id,
    "name": "Portal UT",
    "url": "http://ut.br/editais",
    "source_type": "html",
    "check_frequency_minutes": 60
}
r7 = client.post("/admin/sources", headers=headers_admin, json=source_payload)
results["7_admin_create_source"] = r7.status_code
source_id = r7.json().get("id") if r7.status_code == 200 else None

# 8. criar fonte com institution_id inexistente retorna 400
bad_source = source_payload.copy()
bad_source["institution_id"] = 999999
r8 = client.post("/admin/sources", headers=headers_admin, json=bad_source)
results["8_admin_create_source_bad_inst"] = r8.status_code

# 9. admin lista fontes
r9 = client.get("/admin/sources", headers=headers_admin)
results["9_admin_list_sources"] = r9.status_code

# 10. admin edita fonte
r10 = client.put(f"/admin/sources/{source_id}", headers=headers_admin, json={"check_frequency_minutes": 120})
results["10_admin_edit_source"] = r10.status_code

# 11. admin desativa fonte
r11 = client.delete(f"/admin/sources/{source_id}", headers=headers_admin)
results["11_admin_delete_source"] = r11.status_code
r11_check = client.get(f"/admin/sources/{source_id}", headers=headers_admin)
results["11_check_soft_delete"] = r11_check.json().get("is_active") == False

# clean up
db.query(User).filter(User.email.in_(["common@example.com", "admin@example.com"])).delete(synchronize_session=False)
from app.models.monitored_source import MonitoredSource
from app.models.institution import Institution
if source_id:
    db.query(MonitoredSource).filter(MonitoredSource.id == source_id).delete(synchronize_session=False)
if inst_id:
    db.query(Institution).filter(Institution.id == inst_id).delete(synchronize_session=False)
db.commit()
db.close()

print(json.dumps(results, indent=2))
