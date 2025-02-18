"""Main executor of 'exploit-finder' module."""

__all__ = ("ExploitFinderExecutor",)

import asyncio
from collections import namedtuple

from rich import console, table

from expliot_finder.vulnerability_scanner import VulnerabilityScannerExecutor
from expliot_finder.scraper import FindExploit
from expliot_finder.vulnerability_scanner.ui import display_scanning_progress


# TODO Needs to be refactored in the feature
class ExploitFinderExecutor:
    """This class collect all submodules calls."""

    __slots__ = ("_filtered_kw", "founded_vulnerabilities", "output_table",)

    def __init__(self) -> None:
        """Init ExploitFinderExecutor class."""
        self.filtered_kw: dict[str, str] = {}
        self.founded_vulnerabilities: dict[str, str] = {}
        self.output_table = table.Table(show_lines=True)

    def __call__(self, *args, **kwargs) -> None:
        """Call in right order vulnerability scanners and exploits finder against chosen target."""
        self.scan_selected_device()
        self.find_exploit()
        self.create_output_tb()
        self.show_final_output()

    def __repr__(self) -> str:
        """Print class name and class attributes.

        Returns:
            'ExploitFinderExecutor' as the class name and attributes of
            this class.
        """
        return f"{self.__class__.__name__}({vars(self)!r})"

    @property
    def filtered_kw(self) -> dict[str, str]:
        """Return the filtered parameters provided by the user."""
        return self._filtered_kw

    @filtered_kw.setter
    def filtered_kw(self, cli_kwargs: dict[str, str]) -> None:
        """Filter command line keyword arguments provided by user.

        Args:
            cli_kwargs:
                Command line keyword arguments provided by user.
        """
        self._filtered_kw = {k: v for k, v in cli_kwargs.items() if v is not None}

    def scan_selected_device(self):
        """Run scanners in order to find out what vulnerabilities the selected device to scann has.

        Save results into 'target_vulnerability'
        """
        self.founded_vulnerabilities = asyncio.run(
            VulnerabilityScannerExecutor(**self.filtered_kw)(display_scanning_progress))

    def find_exploit(self):
        """Based on the vulnerabilities found, the scrapper will find suitable exploits."""
        cve_urls, exploit_urls = [], []
        for index_, collected_info in enumerate(
                self.founded_vulnerabilities["ports_services"]):
            if collected_info.service_version != "Unknown":
                cve_urls, exploit_urls = asyncio.run(
                    FindExploit(service_version=collected_info.service_version).run_web_scrappers())

            port_service_vulnerability = namedtuple(
                "Vulnerability",
                "port_number service_name service_version cve_link exploit_link",
            )
            self.founded_vulnerabilities["ports_services"].insert(
                index_ + 1,
                port_service_vulnerability(
                    port_number=collected_info.port_number,
                    service_name=collected_info.service_name,
                    service_version=collected_info.service_version,
                    cve_link=cve_urls[0] if cve_urls else "Unknown",
                    exploit_link=exploit_urls[0]
                    if exploit_urls else "Unknown",
                ),
            )
            del self.founded_vulnerabilities["ports_services"][index_]

            if cve_urls:
                del cve_urls[0]
            if exploit_urls:
                del exploit_urls[0]

    def create_output_tb(self):
        """Create table with all detected ports, services, services versions and found exploits."""
        self.output_table.add_column("PORT", justify="center")
        self.output_table.add_column("SERVICE NAME", justify="center")
        self.output_table.add_column("SERVICE VERSION", justify="center")
        self.output_table.add_column("VULNERABILITY INFORMATION",
                                     justify="center",
                                     header_style="yellow")
        self.output_table.add_column("FOUNDED EXPLOIT",
                                     justify="center",
                                     header_style="red")

        for row in self.founded_vulnerabilities["ports_services"]:
            self.output_table.add_row(
                str(row.port_number),
                row.service_name,
                row.service_version,
                row.cve_link,
                row.exploit_link,
            )

    def show_final_output(self) -> None:
        """Show final output to the end user."""
        console_ = console.Console()
        console_.print(self.output_table)
