# -*- coding: utf-8 -*-
import requests
from lxml import html
from samples import whois_dic
import re
from db_manager import DbManager
import pythonwhois

"""
using package http://cryto.net/pythonwhois/
pip install pythonwhois
"""


class UnknownWhois(Exception):
    pass


class AccessForbidden(Exception):
    pass


class AbsentWhois(Exception):
    pass


# whois databases:
# RIPE (http://www.ripe.net)
# http://www.ripe.net/ripe/docs/ripe-049

# AFRINIC (whois.afrinic.net)
# APNIC (whois.apnic.net)
# ARIN (whois.arin.net)
# LACNIC (whois.lacnic.net)


class WhoisScraper():

    def __init__(self):
        self.ip = None

    def scrape_whois(self, ip_str):
        """
        :param ip_str: ip_address address
        :return: 3-items tuple  (org_name: string, org_address: list of string, country: string) or
            None
        """

        try:
            self.ip = ip_str
            html_page = self.receive_whois_page(ip_str)
            whois_txt = self.extract_whois_text(html_page)
            if whois_txt is None:
                whois = None
            else:
                whois = self.parse_whois(whois_txt)
            return whois
        except UnknownWhois as e:
            self.send_message(e.message)
        except AccessForbidden as e:
            self.send_message(e.message)
        except AbsentWhois as e:
            self.send_message(e.message)

    def receive_whois_page(self, ip_str):
        whois_url = 'http://who.is/whois-ip_address/ip_address-address/%s' %ip_str  # 91.202.128.1
        r = requests.get(whois_url)
        page = r.text
        return page

    def extract_whois_text(self, html_page):
        tree = html.fromstring(html_page)
        item_lst = tree.xpath('//*[@id="domain-data"]/section/section/div/div/pre')
        if len(item_lst) > 0:
            return item_lst[0].text
        else:
            raise AbsentWhois("Can't find whois block in HTML page")

    def parse_whois(self, txt):
        lines = [i.strip() for i in txt.split('\n')]
        # remove heading blank lines
        while len(lines) > 0 and len(lines[0]) == 0:
            lines.pop(0)

        if len(lines) == 0:
            # info was not found
            raise UnknownWhois('The empty whois was loaded')

        if 'This is the RIPE Database query service' in lines[0]:
            # ripe
            return self.parse_apnic_ripe(lines)
        elif '[whois.apnic.net]' in lines[0]:
            #apnic
            return self.parse_apnic_ripe(lines)
        elif 'Joint Whois - whois.lacnic.net' in lines[0]:
            # lacnic
            return self.parse_lacnic(lines)
        elif 'NetRange:' in lines[0]:
            # nameless
            return self.parse_nameless(lines)
        elif len(re.findall("\(NET-\d+-\d+-\d+-\d+-\d+\)", lines[0])) == 1:
            return self.parse_org(lines)
        elif len(lines) == 1 and lines[0] == '0':
            raise AbsentWhois("Can't find whois block in HTML page")
        else:
            # unknown format
            raise UnknownWhois('New format')

    def translate_whois(self, lines):
        """
        :return: list of sections, each section is list of pairs [name, value]
        """
        #delete comments
        l = [i for i in lines if len(i.strip()) == 0 or len(i.strip()) > 0 and (i.strip())[0] != '%']
        #delete blank lines and insert delimiters between sections
        l1 = []
        l2 = []
        new_section = False
        for i in l:
            if len(i) == 0:
                if len(l2) > 0:
                    l1.append(l2)
                l2 = []
                new_section = True
            else:
                if new_section:
                    new_section = False
                l2.append([j.strip() for j in i.split(':', 2)])

        if len(l2) > 0:
            l1.append(l2)

        return l1

    def find_section(self, whois_lst, section_name):
        """
        find section
        :param whois_lst:
        :param section_name:
        :return: list of section
        """
        section = []
        for s in whois_lst:
            if s[0][0] == section_name:
                section.append(s)

        return section

    def find_item(self, whois_section, item_name):
        """
        find all values of item
        :return: list of values
        """
        item_val = []
        for item in whois_section:
            if item[0] == item_name:
                item_val.append(item[1])

        return item_val

    def parse_org(self, lines):
        items = re.split("\(NET-\d+-\d+-\d+-\d+-\d+\)", lines[0])
        if len(items) == 2:
            org_name = items[0]
            org_address = []
            country = ''
            ip_range = self.extract_ip_range(items[1])
        else:
            raise UnknownWhois('New format')

        return org_name, org_address, country, ip_range

    def parse_apnic_ripe(self, lines):
        """ extract whois info: org_name, org_address, country
        it seems apnic and ripe have the same formats
        :param lines: list of text lines
        :return:
        """
        whois_lst = self.translate_whois(lines)
        inetnum_sec = self.find_section(whois_lst, 'inetnum')
        if len(inetnum_sec) == 0:
            raise UnknownWhois('Inetnum section was not found')

        ip_str = self.find_item(inetnum_sec[0], 'inetnum')[0]
        ip_range = self.extract_ip_range(ip_str)
        country = ','.join(self.find_item(inetnum_sec[0], 'country'))
        if len(country) == 0:
            self.send_message("Can't find country in inetnum section")
        org_name = ','.join(self.find_item(inetnum_sec[0], 'descr'))
        if len(org_name) == 0:
            self.send_message("Can't find description in inetnum section")

        org_address = None

        org_sec = self.find_section(whois_lst, 'organisation')
        if len(org_sec) > 1:
            self.send_message('There is more then one organization section')

        if len(org_sec) >= 1:
            # extract data from first organisation section
            org_name = ','.join(self.find_item(org_sec[0], 'org-name')) #rewrite org. name
            if len(org_name) == 0:
                self.send_message("Can't find organisation name in organisation section")
            org_address = self.find_item(org_sec[0], 'address')
            if len(org_address) == 0:
                self.send_message("Can't find organisation address in organisation section")
        else:
            # organization section was not found, search role section
            role_sec = self.find_section(whois_lst, 'role')
            if len(role_sec) >= 1:
                org_name = ','.join(self.find_item(role_sec[0], 'role')) #rewrite org. name
                org_address = self.find_item(role_sec[0], 'address')
            else:
                # role section was not found, search in first person section
                person_sec = self.find_section(whois_lst, 'person')
                if len(person_sec) >= 1:
                    #only address can be extracted
                    org_address = self.find_item(person_sec[0], 'address')
                else:
                    raise UnknownWhois('Unknown whois html page format')

        return org_name, org_address, country, ip_range

    def parse_lacnic(self, lines):
        # TODO: implement
        for l in lines:
            if "You don't have permission to use this service" in l:
                raise AccessForbidden('Access to service is forbidden')

        raise UnknownWhois('New unknown format')

    def parse_nameless(self, lines):
        whois_lst = self.translate_whois(lines)
        org_name_sec = self.find_section(whois_lst, 'OrgName')
        if len(org_name_sec) != 1:
            raise UnknownWhois('Unknown whois format')

        country = ','.join(self.find_item(org_name_sec[0], 'Country'))
        org_name = ','.join(self.find_item(org_name_sec[0], 'OrgName'))

        org_address = self.find_item(org_name_sec[0], 'Address')[0]
        org_city = self.find_item(org_name_sec[0], 'City')[0]
        org_state = self.find_item(org_name_sec[0], 'StateProv')[0]
        org_postal = self.find_item(org_name_sec[0], 'PostalCode')[0]
        full_address = [org_address, org_city, org_state, org_postal]

        net_range_sec = self.find_section(whois_lst, 'NetRange')
        if len(net_range_sec) != 1:
            raise UnknownWhois('Unknown whois format')
        ip_lst = self.find_item(net_range_sec, 'NetRange')
        if len(ip_lst) != 1:
            raise UnknownWhois("Can't find NetRange")
        ip_range = self.extract_ip_range(ip_lst[0])

        return org_name, full_address, country, ip_range

    def extract_ip_range(self, ip_str):
        ip_range = [i.strip() for i in ip_str.split('-')]
        return ip_range

    def between_ip(self, ip, ip1, ip2):
        """
        :param ip: compared ip_address address
        :param ip1:
        :param ip2:
        :return: ip1 <= ip_address <= ip2
        """
        ip_lst = ip.split('.')
        ip1_lst = ip1.split('.')
        ip2_lst = ip2.split('.')
        return ip1_lst <= ip_lst <= ip2_lst

    def send_message(self, msg):
        # TODO: implement
        print ip, msg


def track_whois(visitor_id, ip):
    """

    :param visitor_id: id of the visitor table
    :param ip: visitor ip_address
    :return: nothing
    """
    dbman = DbManager()
    dbman.connect()
    org_id = dbman.find_org_by_ip(ip)
    if org_id is None:
        ws = WhoisScraper()
        whois_tuple = ws.scrape_whois(ip)
        if whois_tuple is not None:
            org_id = dbman.append_new_org(whois_tuple)
            dbman.update_visitor(visitor_id, org_id)
    else:
        dbman.update_visitor(visitor_id, org_id)

    dbman.close()

if __name__ == '__main__':
    wh = WhoisScraper()
    for ip in whois_dic:
        print 'ip_address address:', ip
        print wh.scrape_whois(ip)

    # parse_whois(whois_lst[0]['whois_text'])
    # receive_whois('91.202.128.1')