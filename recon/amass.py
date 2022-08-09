import json
import ipaddress

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.targets import TargetList


@inherits(TargetList)
class AmassScan(ExternalProgramTask):
    """ Run amass scan to perform subdomain enumeration of given domain(s).

    Expects TARGET_FILE.domains file to be a text file with one top-level domain per line.
    If TARGET_FILE.domains file is not present, it is created from TARGET_FILE.

    Note: Process will not run if there is an existing output file, amass.TARGET_FILE.json file that is present.
        It has to be deleted first.

    Commands are similar to the following:

    amass enum -r 8.8.8.8,1.1.1.1 -df tesla -json amass.tesla.json

    Args:
        exempt_list: Path to a file providing blacklisted subdomains, one per line.
        *Required* target_file: specifies the file on disk containing a list of ips or domains
    """

    exempt_list = luigi.Parameter(default="")

    def requires(self):
        """ AmassScan depends on TargetList to run.

        TargetList expects target_file as a parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """
        return TargetList(self.target_file)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"{self.target_file}.amass.json")

    def program_args(self):
        """ Defines the options/arguments sent to amass after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        command = [
            "amass",
            "enum",
            
            # "-ip",
            "-r",
            "8.8.8.8,1.1.1.1",
            # "-passive",

            "-df",
            self.input().path,
            "-json",
            f"{self.target_file}.amass.json",
        ]

        if self.exempt_list:
            command.append("-blf")  # Path to a file providing blacklisted subdomains
            command.append(self.exempt_list)

        return command

@inherits(AmassScan)
class ParseAmassOutput(luigi.Task):
    """ Read amass JSON results and create categorized entries into ip|subdomain files.
        IP files, TARGET_FILE.ips and TARGET_FILE.ip6s, will be used for query by Shodan.

    Args:
        target_file: specifies the file on disk containing a list of ips or domains.
        *Required* exempt_list: Path to a file providing blacklisted subdomains, one per line.
    """

    def requires(self):
        """ ParseAmassOutput depends on AmassScan to run.

        TargetList expects target_file as a parameter.
        AmassScan accepts exempt_list as an optional parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """

        args = {"target_file": self.target_file, "exempt_list": self.exempt_list}
        return AmassScan(**args)

    def output(self):
        """ Returns the target output files for this task.

        Naming conventions for the output files are:
            TARGET_FILE.ips
            TARGET_FILE.ip6s
            TARGET_FILE.subdomains

        Returns:
            dict(str: luigi.local_target.LocalTarget)
        """
        return {
            "target-ips": luigi.LocalTarget(f"{self.target_file}.ips"),
            "target-ip6s": luigi.LocalTarget(f"{self.target_file}.ip6s"),
            "target-subdomains": luigi.LocalTarget(f"{self.target_file}.subdomains"),
        }

    def run(self):
        """ Parse the json file produced by AmassScan and categorize the results into ip|subdomain files.

        An example (prettified) entry from the json file is shown below
            {
                "name":"www.protoslabs.io",
                "domain":"protoslabs.io",
                "addresses": [
                    {
                        "ip":"13.225.0.72",
                        "cidr":"13.225.0.0/21",
                        "asn":16509,
                        "desc":"Xerox Corporation (XEROX-16-Z) - PARC Palo Alto Research Center"
                    },
                    {
                        "ip":"2600:9000:21b4:3600:d:c07c:8840:93a1",
                        "cidr":"2600:9000:21b4::/48",
                        "asn":16509,
                        "desc":"Xerox Corporation (XEROX-16-Z) - PARC Palo Alto Research Center"
                    },
                    {
                        "ip":"2600:9000:21b4:6600:d:c07c:8840:93a1",
                        "cidr":"2600:9000:21b4::/48",
                        "asn":16509,
                        "desc":"Xerox Corporation (XEROX-16-Z) - PARC Palo Alto Research Center"
                    },
                    {
                        "ip":"13.225.0.124",
                        "cidr":"13.225.0.0/21",
                        "asn":16509,
                        "desc":"Xerox Corporation (XEROX-16-Z) - PARC Palo Alto Research Center"
                    }
                ],
                "tag":"dns",
                "sources":[
                    "DNS"
                ]
            }
        """
        unique_ips = set()
        unique_ip6s = set()
        unique_subs = set()

        amass_json = self.input().open()
        ip_file = self.output().get("target-ips").open("w")
        ip6_file = self.output().get("target-ip6s").open("w")
        subdomain_file = self.output().get("target-subdomains").open("w")

        with amass_json as aj, ip_file as ip_out, ip6_file as ip6_out, subdomain_file as subdomain_out:
            for line in aj:
                entry = json.loads(line)
                unique_subs.add(entry.get("name"))

                for address in entry.get("addresses"):
                    ipaddr = address.get("ip")
                    if isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv4Address):  # ipv4 addr
                        unique_ips.add(ipaddr)
                    elif isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv6Address):  # ipv6
                        unique_ip6s.add(ipaddr)

            # send gathered results to their appropriate destination
            for ip in unique_ips:
                print(ip, file=ip_out)

            for sub in unique_subs:
                print(sub, file=subdomain_out)

            for ip6 in unique_ip6s:
                print(ip6, file=ip6_out)
