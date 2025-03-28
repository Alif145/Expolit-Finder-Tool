"""Executor of built-in exploits and CVEs scrappers.

This module will run:
    - 'sites_finder' module
    - 'cve_scrapper' module
in order to find ready exploits and most suitable CVE for captured 'service'
by 'vulnerability_scanner'. Information detected by this module will be saved
and returned to the following form:

    .. code-block:: python

        # Returns URLs to ready exploit that can be used against detected
        # service in target and also URL to CVE's that describe vulnerability
        # in this detected service
         (
            ['https://www.exploit-db.com/exploits/21314']
            ['https://www.cvedetails.com/cve/CVE-2002-1646/'],
         )
"""

__all__ = ("ExploitScrapperExecutor",)

import asyncio
from typing import Optional

from .core import GoogleSitesFinder, SuitableCVEFinder


class ExploitScrapperExecutor:
    """This class is a handle to run: ('sites_finder', 'cve_scrapper') scrappers.

    These modules are run asynchronously in order to find ready exploits and
    most suitable CVE for captured service as quick as possible because the
    module 'vulnerability_scanner' could find a lot of open ports in scanned
    target. If 'vulnerability_scanner' found an open ports there is a high
    probability that's module found also services names and services versions
    for those open ports if so 'ExploitScrapperExecutor' will be called to
    find ready exploits and suitable CVE's for those captured services.

    Attributes:
        service_version:
            Detected service version in a target for which exploit and CVE will
            be searched for.
        google_searcher:
            A 'GoogleSitesFinder' class instance. Methods in this class will be
            used to find ready exploits and CVE's for captured service.
    """

    __slots__ = (
        "service_version",
        "google_searcher",
    )

    def __init__(self, service_version: str) -> None:
        """Init ExploitScrapperExecutor and GoogleSitesFinder classes.

        Args:
            service_version: Single detected service version.
        """
        self.service_version: str = service_version
        self.google_searcher: GoogleSitesFinder = GoogleSitesFinder(service_version)

    def __repr__(self) -> str:
        """Print class name and class attributes.

        Returns:
            'ExploitScrapperExecutor' as the class name and attributes of this
             class.
        """
        return f"{self.__class__.__name__}({vars(self)!r})"

    async def run_web_scrappers(self) -> tuple[Optional[list[str]], list[str]]:
        """Run two modules asynchronously in order to output as fast as possible.

        Theses two modules will run asynchronously:
            - 'sites_finder'
            - 'cve_scrapper'
        to find a ready exploit and most suitable CVE for captured service as
        fast as possible. Module 'vulnerability_scanner' can find a many open
        ports with services in the scanned target. Without asynchronicity, this
        module creates a bottleneck.

        Returns:
            Two URLs, one with a ready exploit for captured service and the
            second one with a most suitable CVE for captured service. This
            'captured service' is a version of captured service that is
            currently iterated in 'main_executor.py' and is provided to this
            class attribute as: 'service_version'.
        """
        cve_urls, exploits_urls = await asyncio.gather(self.scrap_cve(), self.scrap_exploits())
        return cve_urls, exploits_urls

    async def scrap_exploits(self) -> list[str]:
        """Find ready exploits for captured service by using google search engine.

        Ready exploits mean URL to an HTML page with a raw code of exploits
        which to exploit the vulnerabilities in captured service. Search ready
        exploits only in sites with domain: 'https://www.exploit-db.com'.

        Returns:
            URL or URLs to ready exploit/exploits with which to exploit the
            vulnerabilities in captured service.
        """
        return await self.google_searcher.search_for_pages("https://www.exploit-db.com")

    async def scrap_cve(self) -> Optional[list[str]]:
        """Find CVE for captured service by using google search engine.

        CVE document can provide useful information about weakness of captured
        service. Search CVE only in sites with domain: 'https://www.cvedetails.com'.
        It is possible that Google search engine will find a page contain an HTML
        table with a  few CVE's for this captured service if so 'SuitableCVEFinder'
        will be  called to extract most suitable CVE for captured service.

        Returns:
            URL or URLs to CVE/CVE's for captured service.
        """
        cve_table_url: list[str] = await self.google_searcher.search_for_pages(
            "https://www.cvedetails.com"
        )

        if not cve_table_url:
            return cve_table_url

        return await SuitableCVEFinder(cve_table_url[0], self.service_version).find_suitable_cve()
