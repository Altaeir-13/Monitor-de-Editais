import sys
import os
import json
import uuid
import tempfile


USING_TEMP_SQLITE = "DATABASE_URL" not in os.environ
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"monitor_editais_test_crawler_{os.getpid()}.db")

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "monitor_editais_test")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.replace(os.sep, '/')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-crawler-tests-12345")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient

from main import app
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.crawler_run import CrawlerRun
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import create_user
from app.crawler.utils import normalize_title, normalize_url, generate_fingerprint
from app.crawler.spiders.generic_notice_spider import GenericNoticeSpider
from app.crawler.spiders.sigaa_notice_spider import SigaaNoticeSpider
from app.crawler.runner import run_crawler
from app.crawler.spider_factory import get_spider_for_source
from app.api.routers import admin_match as admin_match_router

results = {}
db = SessionLocal()
client = TestClient(app)
if USING_TEMP_SQLITE:
    Base.metadata.create_all(bind=engine)

created_inst_ids = []
created_source_ids = []
created_user_ids = []
existing_active_source_ids = []
original_fetch = GenericNoticeSpider.fetch
original_endpoint_run_crawler = admin_match_router.run_crawler

SIGAA_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sigaa_processos_seletivos.html")
with open(SIGAA_FIXTURE_PATH, "r", encoding="utf-8") as fixture_file:
    SIGAA_HTML_FIXTURE = fixture_file.read()

HTML_FIXTURE = """
<html>
  <body>
    <a href="/noticias">Noticias gerais</a>

    <article>
      <h2>Edital 01/2026 - Processo seletivo para bolsas</h2>
      <a href="editais/edital-01-2026.pdf">Acesse aqui</a>
      <span>Publicado em 20/06/2026</span>
    </article>

    <a href="/cardapio.pdf">Cardapio do restaurante</a>
    <a href="mailto:contato@example.edu.br">Email</a>
    <a href="tel:+550000000000">Telefone</a>
    <a href="javascript:void(0)">Javascript</a>
    <a href="#conteudo">Ancora</a>
  </body>
</html>
"""

try:
    raw_title = "   \nEDITAL DE TESTE\r  2024   "
    results["1_normalize_title"] = normalize_title(raw_title) == "edital de teste 2024"

    base_url = "https://example.com/noticias/"
    results["2_normalize_url_rel"] = normalize_url("edital-1.pdf", base_url) == "https://example.com/noticias/edital-1.pdf"
    results["3_normalize_url_abs"] = normalize_url("/edital-2.pdf", base_url) == "https://example.com/edital-2.pdf"
    results["4_normalize_url_frag"] = normalize_url("https://example.com/page#section", base_url) == "https://example.com/page"

    fp1 = generate_fingerprint(1, "edital teste", "https://example.com")
    fp2 = generate_fingerprint(1, "edital teste", "https://example.com")
    fp3 = generate_fingerprint(2, "edital teste", "https://example.com")
    results["5_fingerprint_deterministic"] = fp1 == fp2
    results["6_fingerprint_unique"] = fp1 != fp3

    spider = GenericNoticeSpider("https://example.edu.br/editais/")
    items = spider.extract(HTML_FIXTURE)
    results["7_spider_extracts_one_notice"] = len(items) == 1
    results["8_spider_uses_context_title"] = items[0]["title"] == "Edital 01/2026 - Processo seletivo para bolsas"
    results["9_spider_resolves_relative_url"] = items[0]["url"] == "https://example.edu.br/editais/editais/edital-01-2026.pdf"
    results["10_spider_ignores_irrelevant_links"] = all("cardapio" not in item["url"] and "noticias" not in item["url"] for item in items)
    results["11_spider_infers_type"] = items[0]["notice_type"] in {"bolsa", "processo_seletivo", "edital"}

    sigaa_spider = SigaaNoticeSpider("https://sigaa.example.edu.br/sigaa/public/processo_seletivo/lista.jsf?aba=p-processo&nivel=S")
    sigaa_items = sigaa_spider.extract(SIGAA_HTML_FIXTURE)
    results["12_sigaa_extracts_table_rows"] = len(sigaa_items) == 2
    results["13_sigaa_keeps_display_url_as_listing"] = sigaa_items[0]["url"] == "https://sigaa.example.edu.br/sigaa/public/processo_seletivo/lista.jsf?aba=p-processo&nivel=S"
    results["14_sigaa_uses_dedupe_url_with_id"] = "id=19215" in sigaa_items[0].get("dedupe_url", "")
    results["15_sigaa_description_has_context"] = all(
        token in (sigaa_items[0].get("description") or "")
        for token in ["Curso:", "Vagas: 36", "Periodo de inscricoes:", "Situacao: Aberto"]
    )

    existing_active_source_ids = [sid for (sid,) in db.query(MonitoredSource.id).filter(MonitoredSource.is_active == True).all()]
    if existing_active_source_ids:
        db.query(MonitoredSource).filter(MonitoredSource.id.in_(existing_active_source_ids)).update(
            {MonitoredSource.is_active: False},
            synchronize_session=False,
        )
        db.commit()

    inst = Institution(
        name="Crawler Test Institution",
        initials="CTI",
        state="PI",
        official_site_url="https://example.edu.br",
        is_active=True,
    )
    db.add(inst)
    db.commit()
    created_inst_ids.append(inst.id)

    success_source = MonitoredSource(
        institution_id=inst.id,
        name="Crawler Success Source",
        url="https://example.edu.br/editais/",
        source_type="HTML_STATIC",
        check_frequency_minutes=1440,
        is_active=True,
    )
    fail_source = MonitoredSource(
        institution_id=inst.id,
        name="Crawler Fail Source",
        url="https://fail.example.edu.br/editais/",
        source_type="HTML_STATIC",
        check_frequency_minutes=1440,
        is_active=True,
    )
    db.add_all([success_source, fail_source])
    db.commit()
    created_source_ids.extend([success_source.id, fail_source.id])

    def mock_fetch(self, url):
        if "fail.example" in self.source_url:
            raise Exception("Simulated network error")
        if "sigaa.example" in self.source_url:
            return SIGAA_HTML_FIXTURE
        return HTML_FIXTURE

    GenericNoticeSpider.fetch = mock_fetch

    first_summary = run_crawler(db)
    notices = db.query(Notice).filter(Notice.source_id == success_source.id).all()
    success_run = db.query(CrawlerRun).filter(CrawlerRun.source_id == success_source.id).order_by(CrawlerRun.id.desc()).first()
    fail_run = db.query(CrawlerRun).filter(CrawlerRun.source_id == fail_source.id).order_by(CrawlerRun.id.desc()).first()
    db.refresh(success_source)
    db.refresh(fail_source)

    results["12_runner_summary_counts"] = first_summary == {
        "sources_checked": 2,
        "items_found": 1,
        "new_items": 1,
        "failed_sources": 1,
    }
    results["13_runner_saves_notice"] = len(notices) == 1 and notices[0].title == "Edital 01/2026 - Processo seletivo para bolsas"
    results["14_runner_saves_absolute_url"] = notices[0].url == "https://example.edu.br/editais/editais/edital-01-2026.pdf"
    results["15_runner_success_run"] = success_run.status == "completed" and success_run.items_found == 1 and success_run.new_items == 1
    results["16_runner_failure_run"] = fail_run.status == "failed" and "Simulated network error" in fail_run.error_message
    results["17_runner_updates_sources"] = success_source.last_success_at is not None and fail_source.last_error_message == "Simulated network error"

    second_summary = run_crawler(db)
    notices_after = db.query(Notice).filter(Notice.source_id == success_source.id).all()
    results["18_runner_prevents_duplicates"] = len(notices_after) == 1 and second_summary["new_items"] == 0
    results["19_runner_keeps_going_after_failure"] = second_summary["sources_checked"] == 2 and second_summary["failed_sources"] == 1
    sigaa_source = MonitoredSource(
        institution_id=inst.id,
        name="Crawler SIGAA Source",
        url="https://sigaa.example.edu.br/sigaa/public/processo_seletivo/lista.jsf?aba=p-processo&nivel=S",
        source_type="SIGAA",
        check_frequency_minutes=1440,
        is_active=True,
    )
    db.add(sigaa_source)
    db.commit()
    created_source_ids.append(sigaa_source.id)

    selected_spider = get_spider_for_source(sigaa_source)
    results["20_factory_selects_sigaa_spider"] = isinstance(selected_spider, SigaaNoticeSpider)

    sigaa_summary = run_crawler(db, source_ids=[sigaa_source.id])
    sigaa_notices = db.query(Notice).filter(Notice.source_id == sigaa_source.id).order_by(Notice.id.asc()).all()
    results["21_runner_saves_sigaa_notices"] = sigaa_summary["new_items"] == 2 and len(sigaa_notices) == 2
    results["22_runner_keeps_sigaa_display_url"] = sigaa_notices[0].url == sigaa_source.url
    results["23_runner_uses_sigaa_dedupe_url_for_normalized_url"] = "id=19215" in sigaa_notices[0].normalized_url
    results["24_runner_sigaa_second_run_no_duplicates"] = run_crawler(db, source_ids=[sigaa_source.id])["new_items"] == 0


    suffix = uuid.uuid4().hex
    common_email = f"crawler_common_{suffix}@example.com"
    admin_email = f"crawler_admin_{suffix}@example.com"

    common_payload = {"name": "Crawler Common", "email": common_email, "password": "123"}
    client.post("/auth/register", json=common_payload)
    common_user = db.query(User).filter(User.email == common_email).first()
    if common_user:
        created_user_ids.append(common_user.id)

    admin_user = create_user(db, UserCreate(name="Crawler Admin", email=admin_email, password="123"))
    admin_user.role = "admin"
    db.commit()
    created_user_ids.append(admin_user.id)

    common_login = client.post("/auth/login", data={"username": common_email, "password": "123"})
    admin_login = client.post("/auth/login", data={"username": admin_email, "password": "123"})
    common_headers = {"Authorization": f"Bearer {common_login.json().get('access_token')}"}
    admin_headers = {"Authorization": f"Bearer {admin_login.json().get('access_token')}"}

    fake_summary = {
        "sources_checked": 3,
        "items_found": 20,
        "new_items": 8,
        "failed_sources": 0,
    }
    admin_match_router.run_crawler = lambda db: fake_summary

    no_token_response = client.post("/admin/run-crawler")
    common_response = client.post("/admin/run-crawler", headers=common_headers)
    admin_response = client.post("/admin/run-crawler", headers=admin_headers)

    results["25_endpoint_requires_token"] = no_token_response.status_code == 401
    results["26_endpoint_requires_admin"] = common_response.status_code == 403
    results["27_endpoint_returns_summary"] = admin_response.status_code == 200 and admin_response.json() == fake_summary

except Exception as e:
    results["error"] = str(e)
finally:
    GenericNoticeSpider.fetch = original_fetch
    admin_match_router.run_crawler = original_endpoint_run_crawler

    for user_id in created_user_ids:
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)

    for source_id in created_source_ids:
        db.query(Notice).filter(Notice.source_id == source_id).delete(synchronize_session=False)
        db.query(CrawlerRun).filter(CrawlerRun.source_id == source_id).delete(synchronize_session=False)
        db.query(MonitoredSource).filter(MonitoredSource.id == source_id).delete(synchronize_session=False)

    for inst_id in created_inst_ids:
        db.query(Institution).filter(Institution.id == inst_id).delete(synchronize_session=False)

    if existing_active_source_ids:
        db.query(MonitoredSource).filter(MonitoredSource.id.in_(existing_active_source_ids)).update(
            {MonitoredSource.is_active: True},
            synchronize_session=False,
        )

    db.commit()
    db.close()
    if USING_TEMP_SQLITE:
        engine.dispose()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

print(json.dumps(results, indent=2))
