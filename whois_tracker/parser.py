#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import socket
from whois_exception import WtWhoisException, WhoisParserException, UnknownWhoisServer, UnknownWhoisFormat
from messanger import WhoisMessanger


ORGNAME = 0
ORGADDRESS = 1
COUNTRY = 2


class ParserManager(object):
    def __init__(self):
        self.whois_parsers = {
            'whois.ripe.net': RipeParser,
            'whois.afrinic.net': None,
            'whois.arin.net': ArinParser,
            'whois.lacnic.net': None,
            'ipmt.rr.com': IpmtrrcomParser,
            'whois.apnic.net': ApnicParser,
        }

    def create_parser(self, ip_address=None, server_url=None, port=43, parser_manager=None):
        """create parser for RIR server
        :param ip_address:
        :param server_url: url of the server
        :param port: rir server port
        :param: parser_parser_manager: the instance of the parser manager
        :return: parser for specified RIR
        """
        if server_url is None:
            server_url, port = self.get_rir_server_url(ip_address)

        if server_url in self.whois_parsers:
            if self.whois_parsers[server_url]:
                parser_instance = self.whois_parsers[server_url](ip_address=ip_address,
                                                                 server_url=server_url,
                                                                 port=port,
                                                                 parser_manager=parser_manager)
                return parser_instance
            else:
                raise UnknownWhoisServer('Parser for %s does not exist' % server_url)
        else:
            raise UnknownWhoisServer('Unknown server %s' % server_url)

    def get_rir_server_url(self, ip_address):
        """
        looking for RIR server for specified ip address
        :param ip_address:
        :return: server url, port number
        """
        data = self.request(ip_address, "whois.iana.org")
        for line in [x.strip() for x in data.splitlines()]:
            match = re.match("refer:\s*([^\s]+)", line)
            if match is None:
                continue
            return match.group(1), 43
        raise WtWhoisException("No root WHOIS server found for domain.")

    def request(self, ip_address, server, port=43):
        """
        read a date from server socket
        :param ip_address: whois ip address
        :param server: rir server
        :param port: rir server port
        :return: string with data read
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sock.send(("%s\r\n" % ip_address).encode("utf-8"))
        buff_lst = []
        while True:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            buff_lst.append(data)
        req = ''.join(buff_lst).decode("utf-8")
        return req

    # def request(self, ip_address, server, port=43):
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     sock.connect((server, port))
    #     sock.send(("%s\r\n" % ip_address).encode("utf-8"))
    #     buff = b""
    #     while True:
    #         data = sock.recv(1024)
    #         if len(data) == 0:
    #             break
    #         buff += data
    #     return buff.decode("utf-8")


class WhoisParser(object):
    """base class for whois parsers"""
    def __init__(self, ip_address, server_url, port=43, comment_char='%', parser_manager=None):
        self._los = []
        self._server_url = server_url
        self._ip_address = ip_address
        self._port = port
        self._comment_char = comment_char
        if parser_manager:
            self._manager = parser_manager
        else:
            self._manager = ParserManager()
        self._raw_whois = None
        self._messanger = WhoisMessanger(self._ip_address, self._server_url, self._port)

    def receive_raw_whois(self):
        """loads information from one of the RIR servers
        :return: whois text loaded from server_url
        """
        # self._raw_whois = whois_request(self._ip_address, self._server_url, self._port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._server_url, self._port))
        sock.send(("%s\r\n" % self._ip_address).encode("utf-8"))
        buff = []
        while True:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            buff.append(data)

        self._raw_whois = (''.join(buff)).decode("utf-8")

        return self._raw_whois

    # def whois_request(self, domain, server, port=43):
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     sock.connect((server, port))
    #     sock.send(("%s\r\n" % domain).encode("utf-8"))
    #     buff = b""
    #     while True:
    #         data = sock.recv(1024)
    #         if len(data) == 0:
    #             break
    #         buff += data
    #     return buff.decode("utf-8")

    def parse(self):
        """ parse whois text and extracts org. name, org. address, country abbreviation

        :return: tuple (org_name: string, org_address: list of string, country: string)
        """
        raise WtWhoisException('Method parse() is not implemented')

    def translate_to_los(self):
        """translate to list of section and write to self._los
        Each section is a list of lines like [val1, val2,..., val_k]
        val1, val2, ... val_k-1 are strings which represent chain of names
        val_k is value
        :return: list of sections
        """
        lines = self.break_to_lines(self._raw_whois)
        self._los = []  # list of sections
        section = []
        new_section = False
        for l in lines:
            if len(l) == 0 or (len(l) > 0 and l[0] == self._comment_char):
                if len(section) > 0:
                    self._los.append(section)
                section = []
                new_section = True
            else:
                if new_section:
                    new_section = False
                section.append([j.strip() for j in l.split(':')])

        if len(section) > 0:
            self._los.append(section)

        return self._los

    def break_to_lines(self, raw_whois):
        """split string to lines and remove white spaces from header and tail
        :param raw_whois: unicode string returned from rir server
        :return: cleaned list of strings
        """
        lines = [i.strip() for i in raw_whois.splitlines()]
        return lines

    def list_le(self, list1, list2):
        """ check that list1 is less or equal to list2 or other words the list1 is equal the head of list2

        :param list1: list of strings
        :param list2: list of strings
        :return: True if less equal; False otherwise
        """
        assert isinstance(list1, tuple) or isinstance(list1, list)
        assert isinstance(list2, tuple) or isinstance(list2, list)
        if len(list1) > len(list2) or len(list1) == 0:
            return False

        if isinstance(list1, tuple) and isinstance(list2,tuple) or isinstance(list1, list) and isinstance(list2, list):
              return list1 == list2[0: len(list1)]
        elif isinstance(list1, tuple) and isinstance(list2, list):
            return list1 == tuple(list2[0: len(list1)])
        elif isinstance(list1, list) and isinstance(list2, tuple):
            return tuple(list1) == list2[0: len(list1)]
        else:
            raise WhoisParserException('Wrong parameters types')

    def find_all_sections(self, section_name):
        """find all section with name = section_name
        a section name is the name of the first line in a section
        :param section_name: list of string
        :return: list of sections
        """
        assert isinstance(section_name, tuple) or isinstance(section_name, list)

        section_lst = []
        for s in self._los:
            if self.list_le(section_name, s[0]):
                section_lst.append(s)

        return section_lst

    def find_first_section(self, section_name):
        """find first section with name = section_name
        :param section_name: list of string
        :return: section or None
        """
        assert isinstance(section_name, tuple) or isinstance(section_name, list)

        for s in self._los:
            if self.list_le(section_name, s[0]):
                return s

        return None

    def find_all_items(self, section, item_name):
        """find all values of item
        :param section: list of [name1, name2,..., value] lines
        :param item_name: list of strings
        :return: list of values or empty list
        """
        assert isinstance(item_name, tuple) or isinstance(item_name, list)

        items_lst = []
        for item in section:
            if self.list_le(item_name, item):
                items_lst.append(item[-1])

        return items_lst

    def find_first_item(self, section, item_name):
        """find first value of item
        :param section: list of [name1, name2,..., value] lines
        :param item_name: list of strings
        :return: item value or None
        """
        assert isinstance(item_name, tuple) or isinstance(item_name, list)

        for item in section:
            if self.list_le(item_name, item):
                val = item[-1]
                return val
        return None

    def extract_ip_range(self, section, name):
        """extracts ip range from strings which look like: organization:ID:NETBLK-ISRR-98.122.128.0-19
        :param section: list of [name1, name2,..., value] lines
        :param name: list of strings
        :return: tuple: ip1, ip2
        """
        for item in section:
            if self.list_le(name, item):
                netblk_str = item[-1]
                ip_lst = re.findall(r"\d+.\d+.\d+.\d+-\d+", netblk_str)
                if len(ip_lst) == 1:
                    ip_from_str, ip_to_str = ip_lst[0].split('-', 1)
                    ip_from = ip_from_str.split('.')
                    ip_to = ip_from[0:-1] + [ip_to_str]
                    return ip_from, ip_to
        return None

    def ip_in_range(self, ip, range):
        """check if ip_address lies in ip_address range
        :param ip: string '98.122.128.10'
        :param range: list of two list - [['98', '122', '128', '0'],['98', '122', '128', '19']]
        :return: True if ip_address is in range, False else
        """
        ip_lst = ip.split('.')
        for i1, i2, i3 in zip(range[0], ip_lst, range[1]):
            if int(i1) == int(i2) and int(i2) == int(i3):
                continue
            elif int(i1) <= int(i2) <= int(i3):
                return True
            else:
                return False


class RipeParser(WhoisParser):
    def __init__(self, *args, **kwargs):
        kwargs['comment_char'] = '%'
        assert kwargs['server_url'] == 'whois.ripe.net'
        super(RipeParser, self).__init__(*args, **kwargs)

    def parse(self):
        """ parse whois text and extracts org. name, org. address, country abbreviation

        :return: tuple (org_name: string, org_address: list of string, country: string)
        """

        nac = [None, [], None]  # name, address, country
        self.translate_to_los()

        # *** inetnum section parsing ***
        inetnum_sec = self.find_all_sections(('inetnum',))
        if len(inetnum_sec) != 1:
            raise UnknownWhoisFormat('Inetnum section was not found or found more than one sections')

        self.parse_inetnum_sec(inetnum_sec[0], nac)

        # *** organization section parsing ***
        org_sec = self.find_all_sections(('organisation',))
        if len(org_sec) >= 1:
            if len(org_sec) > 1:
                self._messanger.send_message('There is more then one organization section')
            # extract data from first organisation section
            self.parse_org_sec(org_sec[0], nac)
        else:
            # organization section was not found, search role section
            role_sec = self.find_all_sections(('role',))
            if len(role_sec) >= 1:
                self.parse_role_sec(role_sec[0], nac)
            else:
                # role section was not found, search in first person section
                person_sec = self.find_all_sections(('person',))
                if len(person_sec) >= 1:
                    self.parse_person_sec(person_sec[0], nac)
                else:
                    raise UnknownWhoisServer('Unknown whois format')

        return nac

    def parse_inetnum_sec(self, inetnum_sec, nac):
        """inetnum section parser. Write org_name and country into nac

        :param inetnum_sec: section
        :param nac: [name, address, country]
        """
        country_lst = self.find_all_items(inetnum_sec, ('country',))
        if len(country_lst) == 0:
            self._messanger.send_message("Can't find country in inetnum section")
        else:
            nac[COUNTRY] = country_lst[0]

        org_name_lst = self.find_all_items(inetnum_sec, ('descr',))
        if len(org_name_lst) == 0:
            self._messanger.send_message("Can't find description in inetnum section")
        else:
            nac[ORGNAME] = org_name_lst[0]

    def parse_org_sec(self, org_section, nac):
        """organization section parser. Write org_name and address to nac

        :param org_sec: section
        :param nac: [name, address, country]
        """
        org_name_lst = self.find_all_items(org_section, ('org-name',))
        if len(org_name_lst) == 0:
            self._messanger.send_message("Can't find organisation name in organisation section")
        else:
            nac[ORGNAME] = org_name_lst[0]

        org_address_lst = self.find_all_items(org_section, ('address',))
        if len(org_address_lst) == 0:
            self._messanger.send_message("Can't find organisation address in organisation section")
        else:
            nac[ORGADDRESS] = org_address_lst

    def parse_role_sec(self, role_section, nac):
        """role section parser. Write org_name, address to nac

        :param role_sec: section
        :param nac: [name, address, country]
        """
        org_name_lst = self.find_all_items(role_section, ('role',))
        if len(org_name_lst) == 0:
            self._messanger.send_message("Can't find organisation name in role section")
        else:
            nac[ORGNAME] = org_name_lst[0]

        org_address_lst = self.find_all_items(role_section, ('address',))
        if len(org_address_lst) == 0:
            self._messanger.send_message("Can't find organisation address in role section")
        else:
            nac[ORGADDRESS] = org_address_lst

    def parse_person_sec(self, person_section, nac):
        """person section parser. Write peson name, address to nac

        :param person_sec: section
        :param nac: [name, address, country]
        """
        person_name = self.find_first_item(person_section, ('person',))

        if person_name is None:
            self._messanger.send_message("Can't find name in person section")
        else:
            nac[ORGNAME] = person_name

        address_lst = self.find_all_items(person_section, ('address',))
        if len(address_lst) == 0:
            self._messanger.send_message("Can't find address in person section")
        else:
            nac[ORGADDRESS] = address_lst


class ArinParser(WhoisParser):
    def __init__(self,  *args, **kwargs):
        kwargs['comment_char'] = '#'
        assert kwargs['server_url'] == 'whois.arin.net'
        super(ArinParser, self).__init__(*args, **kwargs)

    def parse(self):
        """ parse whois text and extracts org. name, org. address, country abbreviation
        :return: nac list: [org_name: string, org_address: list of string, country: string]
        """
        nac = [None, [], None]  # name, address, country

        self.translate_to_los()

        if self.check_simple_org_format():
            org_name = self.parse_arin_simple_org()
            nac[ORGNAME] = org_name
        else:
            ref_ser = self.find_referral_server()
            if ref_ser:
                server_name, port_number = ref_ser
                # raw_whois = self.receive_raw_whois(ip_address, server_name, port_number)
                whois_parser = self._manager.create_parser(self._ip_address, server_name, port_number)
                whois_parser.receive_raw_whois()
                nac = whois_parser.parse()
            else:
                self.parse_arin_org(nac)
        return nac

    def parse_arin_simple_org(self):
        """only organization name can be extracted
        :return: organization name
        """
        items = re.split("\(NET-\d+-\d+-\d+-\d+-\d+\)", self._los[0][0][0])
        if len(items) == 2:
            org_name = items[0]
        else:
            raise UnknownWhoisServer('New format')
        return org_name

    def check_simple_org_format(self):
        """It is simple org format if:
        1) there is exactly one section consists of one line
        2) the first line looks like:
            AT&T Services, Inc. ATT (NET-12-0-0-0-1) 12.0.0.0 - 12.255.255.255
        :return: True if it is simple org format, False else
        """
        if len(self._los) != 1:
            return False
        for sec in self._los:
            for l in sec:
                if len(l) != 1:
                    return False

        fl = self._los[0][0][0]  # first line of first section
        if len(re.findall("\(NET-\d+-\d+-\d+-\d+-\d+\)", fl)) == 1:
            return True
        return False

    def find_referral_server(self):
        """check is ReferralServer section exists. That means the ip_address is used another organization
        for example: "ReferralServer: rwhois://ipmt.rr.com:4321"
        :return: tuple: <referral server string>, <port number>
        """
        s = self.find_first_section(('ReferralServer',))
        if s:
            server = (s[0][2]).lstrip('/')
            port = int(s[0][3])
            return server, port
        else:
            return None

    def parse_arin_org(self, nac):
        """find and parse OrgName section
        :param nac: empty list [org_name: None, org_address: [], country: None]
        :return: filled nac
        """
        s = self.find_first_section(('OrgName',))
        if s is None:
            raise UnknownWhoisFormat('Unknown format')
        org_name = self.find_first_item(s, ('OrgName',))
        org_address = self.find_first_item(s, ('Address',))
        org_city = self.find_first_item(s, ('City',))
        org_state = self.find_first_item(s, ('StateProv',))
        org_postal_code = self.find_first_item(s, ('PostalCode',))
        org_country = self.find_first_item(s, ('Country',))
        nac[ORGNAME] = org_name
        nac[ORGADDRESS] = [org_address, org_city, org_state, org_postal_code]
        nac[COUNTRY] = org_country
        return nac


class IpmtrrcomParser(WhoisParser):
    def __init__(self,  *args, **kwargs):
        kwargs['comment_char'] = '#'
        assert kwargs['server_url'] == 'ipmt.rr.com'
        super(IpmtrrcomParser, self).__init__(*args, **kwargs)

    def parse(self):
        """ parse whois text and extracts org. name, org. address, country abbreviation
        :return: tuple (org_name: string, org_address: list of string, country: string)
        """
        nac = [None, [], None]  # name, address, country

        self.translate_to_los()

        sections = self.find_all_sections(('organization', 'Class-Name', 'organization'))
        for s in sections:
            ip_range = self.extract_ip_range(s, ['organization', 'ID'])
            if self.ip_in_range(self._ip_address, ip_range):
                self.parse_org_sec_ipmt_rr_com(s, nac)
                break
        else: #for else
            raise UnknownWhoisFormat('Organization section was not found')
        return nac

    def parse_org_sec_ipmt_rr_com(self, s, nac):
        """parse organization which looks like:
            organization:Class-Name:organization
            organization:ID:NETBLK-ISRR-98.122.128.0-19
            organization:Auth-Area:98.122.128.0/19
            organization:Org-Name:Road Runner
            organization:Tech-Contact:ipaddreg@rr.com
            organization:Street-Address:8000 1/2 Purfoy Road
            organization:City:Fuquay-Varina
            organization:State:NC
            organization:Postal-Code:27526
            organization:Country-Code:US
        :param s: section
        :param nac: list
        :return: nac
        """
        org_name = self.find_first_item(s, ('organization', 'Org-Name'))
        org_address = self.find_first_item(s, ('organization', 'Street-Address'))
        org_city = self.find_first_item(s, ('organization', 'City'))
        org_state = self.find_first_item(s, ('organization', 'State'))
        org_postal_code = self.find_first_item(s, ('organization', 'Postal-Code'))
        org_country = self.find_first_item(s, ('organization', 'Country-Code'))

        nac[ORGNAME] = org_name
        nac[ORGADDRESS] = [org_address, org_city, org_state, org_postal_code]
        nac[COUNTRY] = org_country

        return nac


class ApnicParser(WhoisParser):
    def __init__(self,  *args, **kwargs):
        kwargs['comment_char'] = '%'
        assert kwargs['server_url'] == 'whois.apnic.net'
        super(ApnicParser, self).__init__(*args, **kwargs)

    def parse(self):
        """ parse whois text and extracts org. name, org. address, country abbreviation
        :return: tuple (org_name: string, org_address: list of string, country: string)
        """
        nac = [None, [], None]  # name, address, country

        self.translate_to_los()
        if self.check_simple_org_format():
            org_name = self.parse_simple_org()
            nac[ORGNAME] = org_name
        else:
            inetnum_sec = self.find_first_section(('inetnum',))
            if inetnum_sec:
                self.check_inetnum(inetnum_sec)
            else:
                raise UnknownWhoisFormat('Inetnum section was not found')

            #looking for address
            role_sec = self.find_first_section(('role',))
            if role_sec:
                self.parse_role(role_sec, nac)
            else:
                person_sec = self.find_first_section(('person',))
                if person_sec:
                    self.parse_person(person_sec, nac)
                else:
                    raise UnknownWhoisFormat('Role and Person sections were not found')

        return nac

    def check_simple_org_format(self):
        """It is simple org format if:
        1) there is exactly one section
        2) each line contains only one item
        3) the first line contains: (NET-<number>-<number>-<number>-<number>-<number>)
        :return: True if it is simple org format, False else
        """
        if len(self._los) != 1:
            return False
        for sec in self._los:
            for l in sec:
                if len(l) != 1:
                    return False

        fl = self._los[0][0][0]  # first line of first section
        if len(re.findall("\(NET-\d+-\d+-\d+-\d+-\d+\)", fl)) == 1:
            return True
        return False

    def parse_simple_org(self):
        """only organization name can be extracted
        :return: organization name
        """
        items = re.split("\(NET-\d+-\d+-\d+-\d+-\d+\)", self._los[0][0][0])
        if len(items) == 2:
            org_name = items[0]
        else:
            raise UnknownWhoisServer('New format')
        return org_name

    def check_inetnum(self, s):
        """extract organization description and country from inetnum section

        :param s: section
        :return: organization description, country
        """
        descr_lst = self.find_all_items(s, ('descr',))
        if len(descr_lst) == 0:
            raise UnknownWhoisFormat('Can not find descr in Inetnum section')
        country = self.find_first_item(s, ('country',))
        if country is None:
            raise UnknownWhoisFormat('Can not find country in Inetnum section')

        return descr_lst, country

    def parse_role(self, s, nac):
        """extracts nac info from role section

        :param s: section
        :param nac: nac list
        :return:
        """
        org_name = self.find_first_item(s, ('role',))
        if org_name is None:
            raise UnknownWhoisFormat('Can not find role in Role section')

        address = self.find_all_items(s, ('address',))
        if len(address) == 0:
            raise UnknownWhoisFormat('Can not find address in Role section')

        country = self.find_first_item(s, ('country',))
        if country is None:
            raise UnknownWhoisFormat('Can not find country in Role section')

        nac[ORGNAME] = org_name
        nac[ORGADDRESS] = address
        nac[COUNTRY] = country
        return nac

    def parse_person(self, s, nac):
        """extracts nac info from person section

        :param s: section
        :param nac: nac list
        :return:
        """
        org_name = self.find_first_item(s, ('person',))
        if org_name is None:
            raise UnknownWhoisFormat('Can not find person in Person section')

        address = self.find_all_items(s, ('address',))
        if len(address) == 0:
            raise UnknownWhoisFormat('Can not find address in Person section')

        country = self.find_first_item(s, ('country',))
        if country is None:
            raise UnknownWhoisFormat('Can not find country in Person section')

        nac[ORGNAME] = org_name
        nac[ORGADDRESS] = address
        nac[COUNTRY] = country
        return nac



if __name__ == '__main__':
    pass