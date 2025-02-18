"""CVE(Common Vulnerabilities and Exposures) scrapper.

Leaning on version of the service that was captured after the target
scanned by 'vulnerability_scanner' module, this module will try to find most
relevant CVE's in web by using scraping technique. If this module find CVE's
the chance to finding a matching exploit increases. Information detected by
this module will be saved and returned in the following form:

    .. code-block:: python

        # Returns URL the most suitable CVE to the captured version of the
        # service
        'https://www.cvedetails.com/cve/CVE-2002-1646/'
"""

__all__ = ("SuitableCVEFinder",)

import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup


class SuitableCVEFinder:
    """Class storing a CVEs scraper that scrap page 'https://www.cvedetails.com'.

    Scrapper in this class will find most relevant CVE for captured service.
    If the script executes methods in this class, it means that 'sites_finder'
    module found page with few CVE's that's are stored in HTML table. The
    purpose of the methods in this class is to extract the best suitable CVE
    for service that was captured after the target was scanned by module named:
    'vulnerability_scanner'.

    Attributes:
        service_version:
            Detected version of the service for which the CVE will be searched for.
        cve_table_url:
            URL to page with an HTML table containing partially matching CVEs
            for the detected service. The scrapper will only pull out the most
            suitable CVE.
    """

    __slots__ = (
        "cve_table_url",
        "service_version",
    )

    def __init__(self, cve_table_url: str, service_version: str) -> None:
        """Init SuitableCVEFinder class.

        Args:
            cve_table_url:
                A page with an HTML table containing partially few CVEs documents.
            service_version:
                Single detected service version.
        """
        self.cve_table_url: str = cve_table_url
        self.service_version: str = service_version

    def __repr__(self) -> str:
        """Print class name and class attributes.

        Returns:
            'SuitableCVEFinder' as the class name and attributes of this class.
        """
        return f"{self.__class__.__name__}({vars(self)!r})"

    def extracted_service_ver_in_nums(self) -> list[str]:
        """Extract only numbers from service version.

        After extracting version of the service only in nums, scraper will be
        able to find the most suitable CVE for captured 'service' from provided
        HTML table with CVE.

        Returns:
            List with a string of numbers from 'service version', without any
            letters or words.
        """
        parsed_service_ver: list[str] = re.split("-|_", self.service_version)
        for element in parsed_service_ver:
            if not any(char.isdigit() for char in element):
                parsed_service_ver.remove(element)
        return parsed_service_ver

    async def get_page_content(self) -> bytes:
        """Create async client session and perform a GET request.

        Perform a GET request to page ('self.cve_table_url') with CVE's stored
        in HTML table.

        Returns: Content of page with few CVE's stored in HTML table.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.cve_table_url) as response:
                return await response.read()

    @staticmethod
    async def scrape_cve_table_page(
        page_content: bytes, parsed_service_ver: list[str]
    ) -> Optional[str]:
        """Scrape provided HTML table to find most suitable CVE for detected service.

        The 'page_content' will hold a page with an HTML table filled with all
        CVE's which partially match service. 'Partially' means that this HTML
        table was found by 'sites_finder' module and this module was looking
        for CVE by 'service name' not exactly by 'service version'. So this
        HTML table will store few CVE's for different versions of captured
        service and this scrapper will extract best matching CVE by searching
        for the exact version of the captured service. Provide page in pram:
        'page_content' must be from domain: (https://www.cvedetails.com).

        Args:
            parsed_service_ver:
                List with a string of numbers from 'service version',
                without any letters or words. Using the version of the service
                prepared in this way, the scraper will find the most suitable
                CVE for this captured service.
            page_content:
                Content of page from domain: 'https://www.cvedetails.com'
                with few CVE's stored in HTML table that partially match
                service.

        Returns:
            URL the most suitable CVE to the captured version of the service.
        """
        soup = BeautifulSoup(page_content.decode("UTF-8"), "html.parser")

        for element in soup.find_all("td", class_="cvesummarylong"):
            if any(word in element.text for word in parsed_service_ver):
                cve_a_tag = (
                    element.find_previous()
                    .find_previous()
                    .find_parent()
                    .find("td")
                    .find_next("td")
                    .find("a")
                )
                return f"https://www.cvedetails.com{cve_a_tag['href']}"
        return None

    async def find_suitable_cve(self) -> Optional[list[str]]:
        """Run sequence of functions to start scraping a provided HTML page with CVEs.

        This handle will execute functions in following order which:
            - Extract the numbers from the version of the service that will be
             used to find the most suitable CVE.
            - Asynchronously get the whole content of the HTML table with links
                to CVEs.
            - Using an extracted numbers from captured service version,
                asynchronously scrape already downloaded HTML table page in
                order to find most suitable CVE for captured service.

        Returns:
            One single URL to most suitable CVE for captured 'service'.
        """
        parsed_service_ver: list[str] = self.extracted_service_ver_in_nums()
        page_content: bytes = await self.get_page_content()

        if suitable_cve := await self.scrape_cve_table_page(page_content, parsed_service_ver):
            return [suitable_cve]
        return None
