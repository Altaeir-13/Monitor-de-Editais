import sys
import os
import json

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.db.session import SessionLocal
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.crawler_run import CrawlerRun
from app.crawler.utils import normalize_title, normalize_url, generate_fingerprint
from app.crawler.spiders.test_spider import TestSpider
from app.crawler.runner import run_crawler

results = {}
db = SessionLocal()

try:
    # 1. Normalization tests
    raw_title = "   \nEDITAL DE TESTE\r  2024   "
    results["1_normalize_title"] = (normalize_title(raw_title) == "edital de teste 2024")
    
    base_url = "https://example.com/noticias/"
    results["2_normalize_url_rel"] = (normalize_url("edital-1.pdf", base_url) == "https://example.com/noticias/edital-1.pdf")
    results["3_normalize_url_abs"] = (normalize_url("/edital-2.pdf", base_url) == "https://example.com/edital-2.pdf")
    results["4_normalize_url_frag"] = (normalize_url("https://example.com/page#section", base_url) == "https://example.com/page")

    # 2. Fingerprint tests
    fp1 = generate_fingerprint(1, "edital teste", "https://example.com")
    fp2 = generate_fingerprint(1, "edital teste", "https://example.com")
    fp3 = generate_fingerprint(2, "edital teste", "https://example.com")
    results["5_fingerprint_deterministic"] = (fp1 == fp2)
    results["6_fingerprint_unique"] = (fp1 != fp3)

    # 3. Spider Extraction using Mock
    html_fixture = """
    <html>
        <body>
            <div class="notice-item"><a href="/edital-1">Edital 01/2024</a></div>
            <div class="notice-item"><a href="/edital-2">   Edital 02/2024   </a></div>
            <div><a href="/not-a-notice">Not a notice</a></div>
        </body>
    </html>
    """
    spider = TestSpider("http://dummy.url")
    items = spider.extract(html_fixture)
    results["7_spider_extracts_correct_count"] = (len(items) == 2)
    results["8_spider_extracts_data"] = (items[0]["title"] == "Edital 01/2024" and items[0]["url"] == "/edital-1")

    # 4. Engine Run Test (Mocked fetch)
    inst = Institution(
        name="Inst Test", 
        initials="IT", 
        state="PI",
        official_site_url="https://example.edu.br",
        is_active=True
    )
    db.add(inst)
    db.commit()
    
    source = MonitoredSource(
        institution_id=inst.id, 
        name="Test Source", 
        url="https://example.com", 
        source_type="html",
        check_frequency_minutes=1440,
        is_active=True
    )
    db.add(source)
    db.commit()

    original_fetch = TestSpider.fetch
    try:
        # Monkeypatch fetch on TestSpider
        def mock_fetch(self, url):
            return """<div class="notice-item"><a href="link1">Notice 1</a></div>"""
        TestSpider.fetch = mock_fetch

        # Clean existing notices
        db.query(Notice).filter(Notice.source_id == source.id).delete()
        db.query(CrawlerRun).filter(CrawlerRun.source_id == source.id).delete()
        db.commit()

        # Run crawler
        run_crawler(db)

        # Validate db state
        notices = db.query(Notice).filter(Notice.source_id == source.id).all()
        results["9_crawler_saves_notice"] = (len(notices) == 1 and notices[0].title == "Notice 1")
        
        run_rec = db.query(CrawlerRun).filter(CrawlerRun.source_id == source.id).order_by(CrawlerRun.id.desc()).first()
        results["10_crawler_run_success"] = (run_rec.status == "completed" and run_rec.new_items == 1)
        
        db.refresh(source)
        results["11_source_last_checked_updated"] = (source.last_checked_at is not None)
        results["12_source_last_success_updated"] = (source.last_success_at is not None)

        # Run again to test duplicate prevention
        run_crawler(db)
        
        notices_after = db.query(Notice).filter(Notice.source_id == source.id).all()
        results["13_duplicate_prevention_notice"] = (len(notices_after) == 1)
        
        run_rec2 = db.query(CrawlerRun).filter(CrawlerRun.source_id == source.id).order_by(CrawlerRun.id.desc()).first()
        results["14_duplicate_prevention_run"] = (run_rec2.status == "completed" and run_rec2.new_items == 0 and run_rec2.items_found == 1)

        # 5. Engine Run Test (Failure)
        def mock_fetch_fail(self, url):
            raise Exception("Simulated network error")
        TestSpider.fetch = mock_fetch_fail

        run_crawler(db)
        run_rec3 = db.query(CrawlerRun).filter(CrawlerRun.source_id == source.id).order_by(CrawlerRun.id.desc()).first()
        
        results["15_crawler_run_failure"] = (run_rec3.status == "failed" and "Simulated network error" in run_rec3.error_message)
        
        db.refresh(source)
        results["16_source_last_error_updated"] = (source.last_error_message == "Simulated network error")

    finally:
        # Cleanup mock
        TestSpider.fetch = original_fetch
        
        # Cleanup DB
        db.query(Notice).filter(Notice.source_id == source.id).delete()
        db.query(CrawlerRun).filter(CrawlerRun.source_id == source.id).delete()
        db.delete(source)
        db.delete(inst)
        db.commit()

except Exception as e:
    results["error"] = str(e)
finally:
    db.close()

print(json.dumps(results, indent=2))
