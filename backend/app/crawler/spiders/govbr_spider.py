from app.crawler.spiders.paginated_spider import PaginatedNoticeSpider


class GovBrNoticeSpider(PaginatedNoticeSpider):
    """
    Gov.br and Plone portals usually expose notice listings as server-rendered
    HTML collections with simple pagination, so the paginated generic strategy
    is the safest first layer.
    """

    pass