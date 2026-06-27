from urllib.parse import urlparse

from app.crawler.spiders.generic_notice_spider import GenericNoticeSpider
from app.crawler.spiders.govbr_spider import GovBrNoticeSpider
from app.crawler.spiders.paginated_spider import PaginatedNoticeSpider
from app.crawler.spiders.wordpress_spider import WordPressNoticeSpider


def get_spider_for_source(source):
    source_type = (source.source_type or "").upper()
    host = urlparse(source.url).netloc.lower()

    if source_type in {"WORDPRESS", "WORDPRESS_ARCHIVE"}:
        return WordPressNoticeSpider(source_url=source.url)

    if source_type in {"GOVBR", "PLONE", "GOVBR_COLLECTION"} or "gov.br" in host:
        return GovBrNoticeSpider(source_url=source.url)

    if source_type in {"PAGINATED_HTML", "HTML_PAGINATED", "TABLE_HTML", "PROCESS_SELECTION_PORTAL"}:
        return PaginatedNoticeSpider(source_url=source.url)

    if "wp-content" in host or "wordpress" in host:
        return WordPressNoticeSpider(source_url=source.url)

    return GenericNoticeSpider(source_url=source.url)