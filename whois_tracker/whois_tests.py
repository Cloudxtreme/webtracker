#!/usr/bin/python
# -*- coding: utf-8 -*-

#import random
import unittest
import MySQLdb
from datetime import datetime
#from MySQLdb import IntegrityError
#from _mysql_exceptions import IntegrityError
from whois import WhoisTracker, handle_whois_queue
from home.tasks import find_whois
from whois_tracker.parser import ParserManager
from whois_tracker.whois_exception import WtWhoisException, WhoisParserException, UnknownWhoisServer, UnknownWhoisFormat
from whois_tracker.parser import RipeParser, ApnicParser, ArinParser, IpmtrrcomParser, WhoisParser
from whois_tracker.samples import whois_dic
from db_manager import DbManager
import webtracker.settings as parms
from db_manager import dict_fetchall
from messanger import send_whois_message
from whois import is_whois_locked, lock_whois
from MySQLdb import connect
from webtracker.settings import DB_PARMS



output = {


    ('91.202.128.2', 'whois.ripe.net'): [
            'Kyiv National Taras Shevchenko University',
            ['Kyiv University,', 'Volodymyrska, 64 01033 Kyiv, UA'],
            'UA'
        ],
    ('94.222.128.2', 'whois.ripe.net'): [
            'Mannesmann Arcor Network Operation Center',
            ['Arcor AG & Co. KG', 'Department TBS', 'Otto-Volger-Str. 19', 'D-65843 Sulzbach/Ts.', 'Germany'],
            'DE'
        ],
    ('0.0.0.1', 'whois.ripe.net'): [
            'Roman Sinyuk',
            ['Taras Shevchenko Kiev University', '01033 Kiev,Ukraine', 'Volodymyrska st, 64'],
            'UA'
        ],
    ('12.100.128.1', 'whois.arin.net'): ['AT&T Services, Inc. ATT ', [], None],

    ('50.212.128.1', 'whois.arin.net'): ['Comcast Cable Communications Holdings, Inc CCCH3-4 ', [], None],

    ('99.202.128.1', 'whois.arin.net'): ['Sprint Nextel Corporation', ['6391 Sprint Parkway', 'Overland Park', 'KS', '66251-4300'], 'US'],

    ('98.122.128.1', 'ipmt.rr.com'): ['Road Runner', ['8000 1/2 Purfoy Road', 'Fuquay-Varina', 'NC', '27526'], 'US'],

    ('150.212.128.1', 'whois.apnic.net'): ['University of Pittsburgh PITTNET-3 ', [], None],

    ('220.224.128.1', 'whois.apnic.net'): [u'Antiabuse Helpdesk',
                                           [u'Reliance Communication Ltd',
                                            u'Antiabuse Helpdesk, 2nd Floor,',
                                            u'International Area , A Block',
                                            u'Dhirubai Ambani Knowledge City,',
                                            u'Thane Belapur Road, KoparKhairane,',
                                            u'Navi Mumbai - 400710'
                                           ],
                                           u'IN'
    ]

}

not_exist_lst = ['0.0.0.1', '150.212.128.1']


class TestLockUtils(unittest.TestCase):
    def setUp(self):
        test_db_name = 'whoistest_' + parms.DB_PARMS['db']
        parms.DB_PARMS['db'] = test_db_name

    def tearDown(self):
        db_name = parms.DB_PARMS['db']
        assert len(db_name) > len('whoistest_') and 'whoistest_' == db_name[0:len('whoistest_')]
        parms.DB_PARMS['db'] = db_name[len('whoistest_'):]

    def test_lock(self):
        lock_whois(True)
        conn = connect(**DB_PARMS)
        try:
            cur = conn.cursor()
            cur.execute(""" select lock_on from wt_queue_lock; """)
            rs = cur.fetchall()
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0][0], 1)

        finally:
            conn.close()

        self.assertTrue(is_whois_locked())

        lock_whois(False)
        conn = connect(**DB_PARMS)
        try:
            cur = conn.cursor()
            cur.execute(""" select lock_on from wt_queue_lock; """)
            rs = cur.fetchall()
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0][0], 0)
        finally:
            conn.close()

        self.assertFalse(is_whois_locked())

        lock_whois(True)
        self.assertFalse(handle_whois_queue())

        lock_whois(False)
        self.assertTrue(handle_whois_queue())


class TestWhois(unittest.TestCase):

    def setUp(self):
        test_db_name = 'whoistest_' + parms.DB_PARMS['db']
        parms.DB_PARMS['db'] = test_db_name

    def tearDown(self):
        db_name = parms.DB_PARMS['db']
        assert len(db_name) > len('whoistest_') and 'whoistest_' == db_name[0:len('whoistest_')]
        parms.DB_PARMS['db'] = db_name[len('whoistest_'):]

    def testParserManager(self):
        par_man = ParserManager()

        parser = par_man.create_parser(ip_address='91.202.128.2', server_url='whois.ripe.net', port=43)
        pass

        server_lst = [
            ('91.202.128.2', 'whois.ripe.net', 43, '%', RipeParser,),
            ('99.202.128.1', 'whois.arin.net', 43, '#', ArinParser,),
            ('98.122.128.1', 'ipmt.rr.com', 4321, '#', IpmtrrcomParser,),
            ('220.212.128.1', 'whois.apnic.net', 43, '%',  ApnicParser,)

        ]
        for ip_address, server_url, port, com_char, par_class in server_lst:
            parser = par_man.create_parser(ip_address=ip_address, server_url=server_url, port=port, parser_manager=par_man)
            self.assertIsInstance(parser, par_class)
            self.assertEqual(parser._server_url, server_url)
            self.assertEqual(parser._comment_char, com_char)
            self.assertIs(parser._manager, par_man)

        not_implement_lst = [
            'whois.afrinic.net',
            'whois.lacnic.net',
        ]
        for server_url in not_implement_lst:
                self.assertRaisesRegexp(UnknownWhoisServer, 'does not exist', par_man.create_parser, ip_address=None,
                                        server_url=server_url, port=None, parser_manager=par_man)

        self.assertRaisesRegexp(UnknownWhoisServer, 'Unknown server', par_man.create_parser, ip_address=None,
                                        server_url='********', port=None, parser_manager=par_man)

        parser = par_man.create_parser(ip_address='91.202.128.2', server_url=None, port=None, parser_manager=par_man)
        self.assertIsInstance(parser, RipeParser)

    def create_base_parser(self, comment_char='%'):
        parser = WhoisParser(ip_address=None, server_url=None, port=None, comment_char=comment_char, parser_manager=None)
        return parser

    def testWhoisParser(self):
        parser = self.create_base_parser()  # WhoisParser('', ParserManager(), '%')

        parser._raw_whois = ''
        parser.translate_to_los()
        self.assertListEqual(parser._los, [])

        parser._raw_whois = '%comment \n % comment \n \n \n'
        parser.translate_to_los()
        self.assertListEqual(parser._los, [])

        parser._raw_whois = "section: section name \n oreganization: ibm company"
        parser.translate_to_los()
        whois_lst = [[['section', 'section name'], ['oreganization', 'ibm company']]]
        self.assertListEqual(parser._los, whois_lst)

        parser._raw_whois = "section1: section name \n oreganization: ibm company\n \n section2: 2 \n city: kiev"
        parser.translate_to_los()
        whois_lst = [[['section1', 'section name'], ['oreganization', 'ibm company']],
                     [['section2', '2'], ['city', 'kiev']]]
        self.assertListEqual(parser._los, whois_lst)

        parser._raw_whois = "section1: subsection1: section name \n oreganization:name:main name: ibm company\n \n section2: 2 \n city: kiev"
        parser.translate_to_los()
        whois_lst = [[['section1', 'subsection1', 'section name'], ['oreganization', 'name', 'main name', 'ibm company']],
                     [['section2', '2'], ['city', 'kiev']]]
        self.assertListEqual(parser._los, whois_lst)

    def testListLe(self):
        parser = self.create_base_parser()

        self.assertFalse(parser.list_le([], []))
        self.assertFalse(parser.list_le([], ['section']))
        self.assertFalse(parser.list_le(['role'], ['section']))
        self.assertTrue(parser.list_le(['role'], ['role']))
        self.assertTrue(parser.list_le(['role'], ['role', 'section']))
        self.assertTrue(parser.list_le(['role', 'section'], ['role', 'section']))
        self.assertTrue(parser.list_le(['role', 'section'], ['role', 'section', 'address']))
        self.assertFalse(parser.list_le(['role', 'section'], ['role', 'section1', 'address']))

    def testFindSections(self):
        whois_lst = [
            [
                ['section', 'subsection', 'section name'],
                ['organization', 'name', 'main name', 'ibm company']
            ],
            [
                ['section', '2'],
                ['city', 'kiev'],
            ],

            [
                ['section', 'subsection', 'section name 2'],
                ['organization', 'name', 'main name', 'google company']
            ],

            [
                ['role', 'section', 'network'],
                ['class', 'abc']

            ]
        ]
        parser = self.create_base_parser()

        parser._los = whois_lst
        lst = [
            [
                ['section', 'subsection', 'section name'],
                ['organization', 'name', 'main name', 'ibm company']
            ],
            [
                ['section', '2'],
                ['city', 'kiev'],
            ],

            [
                ['section', 'subsection', 'section name 2'],
                ['organization', 'name', 'main name', 'google company']
            ],

        ]
        self.assertListEqual(parser.find_all_sections(['section']), lst)
        lst = [[['section', 'subsection', 'section name'], ['organization', 'name', 'main name', 'ibm company']],
               [['section', 'subsection', 'section name 2'], ['organization', 'name', 'main name', 'google company']]]
        self.assertListEqual( parser.find_all_sections(['section', 'subsection']), lst)

        lst = [
            [
                ['role', 'section', 'network'],
                ['class', 'abc']

            ]
        ]

        self.assertListEqual(parser.find_all_sections(['role']), lst)
        self.assertListEqual(parser.find_all_sections(['role1']), [])

        lst = [['role', 'section', 'network'], ['class', 'abc']]
        self.assertListEqual(parser.find_first_section(['role']), lst)

        lst = [
                ['section', 'subsection', 'section name'],
                ['organization', 'name', 'main name', 'ibm company']
            ]

        self.assertListEqual(parser.find_first_section(['section']), lst)

        self.assertIsNone(parser.find_first_section(['sectioniiii']))

    def testFindItems(self):
        whois_lst = [
            [
                ['section', 'subsection', 'section name'],
                ['organization', 'name', 'main name', 'ibm company'],
                ['organization', 'name', 'main name', 'california'],
                ['organization', 'name', 'main name', 'usa'],
            ],
            [
                ['section', '2'],
                ['city', 'kiev'],
            ],

            [
                ['section', 'subsection', 'section name 2'],
                ['organization', 'name', 'main name', 'google company']
            ],

            [
                ['role', 'section', 'network'],
                ['class', 'abc']

            ]
        ]

        parser = self.create_base_parser()
        parser._los = whois_lst
        s = parser._los[0]
        self.assertListEqual(parser.find_all_items(s, ['section']), ['section name'])
        self.assertListEqual(parser.find_all_items(s, ['organization']), ['ibm company', 'california', 'usa'])
        self.assertIsNone(parser.find_first_item(s, ['organization___']))
        self.assertEqual(parser.find_first_item(s, ['organization']), 'ibm company')

    def testIpRangeExtraction(self):
        parser = self.create_base_parser()
        s = [
                ['organization', 'Class-Name', 'organization'],
                ['organization', 'ID', 'NETBLK-ISRR-98.122.128.0-19'],
                ['organization', 'Auth-Area', '98.122.128.0/19'],
                ['organization', 'Org-Name', 'Road Runner'],
                ['organization', 'Tech-Contact', 'ipaddreg@rr.com'],
                ['organization', 'Street-Address', '8000 1/2 Purfoy Road'],
                ['organization', 'City', 'Fuquay-Varina'],
                ['organization', 'State', 'NC'],
                ['organization', 'Postal-Code', '27526'],
                ['organization', 'Country-Code', 'US'],
        ]
        self.assertEqual(parser.extract_ip_range(s, ['organization', 'ID']),
                         (['98', '122', '128', '0'], ['98', '122', '128', '19']))

        self.assertTrue(parser.ip_in_range('98.122.128.19', [['98', '122', '128', '0'],['98', '122', '128', '19']]))
        self.assertTrue(parser.ip_in_range('98.122.128.0', [['98', '122', '128', '0'],['98', '122', '128', '19']]))
        self.assertTrue(parser.ip_in_range('98.122.128.10', [['98', '122', '128', '0'],['98', '122', '128', '19']]))
        self.assertFalse(parser.ip_in_range('98.122.128.29', [['98', '122', '128', '0'],['98', '122', '128', '19']]))
        self.assertFalse(parser.ip_in_range('98.123.128.19', [['98', '122', '128', '0'],['98', '122', '128', '19']]))
        self.assertFalse(parser.ip_in_range('99.122.128.19', [['98', '122', '128', '0'],['98', '122', '128', '19']]))

    def testRipeParser(self):
        par_man = ParserManager()

        parser = par_man.create_parser('91.202.128.2', 'whois.ripe.net')
        parser._raw_whois = whois_dic['91.202.128.2']
        output_Kyiv_University = [
            'Kyiv National Taras Shevchenko University',
            ['Kyiv University,', 'Volodymyrska, 64 01033 Kyiv, UA'],
            'UA'
        ]
        self.assertListEqual(parser.parse(), output_Kyiv_University)

        parser = par_man.create_parser('94.222.128.2', 'whois.ripe.net')
        parser._raw_whois = whois_dic['94.222.128.2']
        output_Arcor_AG = [
            'Mannesmann Arcor Network Operation Center',
            ['Arcor AG & Co. KG', 'Department TBS', 'Otto-Volger-Str. 19', 'D-65843 Sulzbach/Ts.', 'Germany'],
            'DE'
        ]
        self.assertListEqual(parser.parse(), output_Arcor_AG)

        # print par_man.get_rir_server_url('97.222.128.2') - arin

        parser = par_man.create_parser('0.0.0.1', 'whois.ripe.net')
        parser._raw_whois = whois_dic['0.0.0.1']
        output_Kiev_University_2 = [
            'Roman Sinyuk',
            ['Taras Shevchenko Kiev University', '01033 Kiev,Ukraine', 'Volodymyrska st, 64'],
            'UA'
        ]
        self.assertListEqual(parser.parse(), output_Kiev_University_2)

    def testArinParser(self):
        par_man = ParserManager()
        server = 'whois.arin.net'

        output_ATServices = ['AT&T Services, Inc. ATT ', [], None]
        self.assert_parser(par_man, '12.100.128.1', server, output_ATServices)

        output_Comcast = ['Comcast Cable Communications Holdings, Inc CCCH3-4 ', [], None]
        self.assert_parser(par_man, '50.212.128.1', server, output_Comcast)

        output_Sprint = ['Sprint Nextel Corporation', ['6391 Sprint Parkway', 'Overland Park', 'KS', '66251-4300'], 'US']
        self.assert_parser(par_man, '99.202.128.1', server, output_Sprint)

        output_Road_Runner = ['Road Runner', ['8000 1/2 Purfoy Road', 'Fuquay-Varina', 'NC', '27526'], 'US']
        self.assert_parser(par_man, '98.122.128.1', 'ipmt.rr.com', output_Road_Runner)
        self.assert_parser(par_man, '98.122.128.1', server, output_Road_Runner)

    def testApnicParser(self):
        par_man = ParserManager()
        server = 'whois.apnic.net'

        output_Univ_Pittsburgh = ['University of Pittsburgh PITTNET-3 ', [], None]
        self.assert_parser(par_man, '150.212.128.1', server, output_Univ_Pittsburgh)

        output_CHINANET_SICHUAN = ['CHINANET SICHUAN', ['No.72,Wen Miao Qian Str Chengdu SiChuan PR China'], 'CN']
        self.assert_parser(par_man, '220.224.128.1', server, output_CHINANET_SICHUAN)

    def assert_parser(self, par_manager, ip_addres, whois_server, output = None):
        """

        :param par_manager:
        :param ip_addres: e (server_url, ip) or ip
        :param whois_server:
        :param output:
        :return:
        """
        parser = par_manager.create_parser(ip_addres, whois_server)
        if (whois_server, ip_addres) in whois_dic:
            #looking by full address (server, ip)
            parser._raw_whois = whois_dic[(whois_server, ip_addres)]
        else:
            parser._raw_whois = whois_dic[ip_addres]
        if output is None:
            print parser.parse()
        else:
            self.assertListEqual(parser.parse(), output)

    def testDbManager_append(self):
        db = DbManager()
        db.connect()
        try:
            db.clear_db()

            ### Test organization table ###

            # ('91.202.128.2', 'whois.ripe.net'): [
            #             'Kyiv National Taras Shevchenko University',
            #             ['Kyiv University,', 'Volodymyrska, 64 01033 Kyiv, UA'],
            #             'UA'
            #         ],
            ip_kiev_univ = ('91.202.128.2', 'whois.ripe.net')
            kiev_univ_id = db.append_org(*output[ip_kiev_univ])
            written_id = db.find_org('Kyiv National Taras Shevchenko University', 'UA')
            self.assertEqual(kiev_univ_id, written_id)

            none_id = db.find_org('Kyiv National Taras Shevchenko University', 'UA************')
            self.assertIsNone(none_id)

            self.assertRaises(MySQLdb.IntegrityError, db.append_org, *output[ip_kiev_univ])

            # ('94.222.128.2', 'whois.ripe.net'): [
            #             'Mannesmann Arcor Network Operation Center',
            #             ['Arcor AG & Co. KG', 'Department TBS', 'Otto-Volger-Str. 19', 'D-65843 Sulzbach/Ts.', 'Germany'],
            #             'DE'
            #         ],
            ip_mannesmann_arcor = ('94.222.128.2', 'whois.ripe.net')
            mannesmann_arcor_id = db.append_org(*output[ip_mannesmann_arcor])
            written_id = db.find_org('Mannesmann Arcor Network Operation Center', 'DE')
            self.assertEqual(mannesmann_arcor_id, written_id)

            self.assertEqual(db.append_new_org(*output[ip_mannesmann_arcor]), written_id)

            # ('99.202.128.1', 'whois.arin.net'):
            # ['Sprint Nextel Corporation', ['6391 Sprint Parkway', 'Overland Park', 'KS', '66251-4300'], 'US'],
            ip_sprint_nextel = ('99.202.128.1', 'whois.arin.net')
            sprint_nextel_id = db.append_new_org(*output[ip_sprint_nextel])
            written_id = db.find_org('Sprint Nextel Corporation', 'US')
            self.assertEqual(sprint_nextel_id, written_id)

            ### Test Ip table ###
            #ip_kiev_univ = ('91.202.128.2', 'whois.ripe.net')
            kiev_univ_ip_id = db.append_ip('91.202.128.2', kiev_univ_id)
            written_id = db.find_ip('91.202.128.2', kiev_univ_id)
            self.assertEqual(kiev_univ_ip_id, written_id)

            none_id = db.find_ip('91.202.128.*', kiev_univ_ip_id)
            self.assertIsNone(none_id)

            self.assertRaises(MySQLdb.IntegrityError, db.append_ip, '91.202.128.2', kiev_univ_id)
            # self.assertRaises(MySQLdb.IntegrityError, db.append_ip, '91.202.128.2', mannesmann_arcor_id)

            mannesmann_arcor_ip_id = db.append_ip('94.222.128.2', mannesmann_arcor_id)
            written_id = db.find_ip('94.222.128.2', mannesmann_arcor_id)
            self.assertEqual(mannesmann_arcor_ip_id, written_id)

            none_id = db.find_ip('91.202.128.*', mannesmann_arcor_id)
            self.assertIsNone(none_id)

            kiev_univ_ip_id = db.append_new_ip('91.202.128.2', kiev_univ_id)
            written_id = db.find_ip('91.202.128.2', kiev_univ_id)
            self.assertEqual(kiev_univ_ip_id, written_id)

            # ('99.202.128.1', 'whois.arin.net'): ['Sprint Nextel Corporation', ['6391 Sprint Parkway', 'Overland Park', 'KS', '66251-4300'], 'US'],
            sprint_nextel_ip_id = db.append_new_ip('99.202.128.1', None)
            written_id = db.find_ip('99.202.128.1', None)
            self.assertEqual(sprint_nextel_ip_id, written_id)

            ### Test Visitor table ###
            visitor_ip = '1.1.1.1'
            referer_url = ''
            page_url = 'knu.com'
            datetime_of_visit = datetime.today()
            organization_ip_id = kiev_univ_ip_id
            visitor_id = db.append_visitor(referer_url, page_url, datetime_of_visit, organization_ip_id)
            self.assertIsNotNone(visitor_id)

            # org_id = db.find_org_by_ip(visitor_ip)
            # self.assertEqual(mannesmann_arcor_id, org_id)

        finally:
            db.close()

    def testDbManager_search(self):
        ws = WhoisTracker()
        # TODO: correctly process 150.212.128.1
        # nac = ws.search_whois('220.224.128.1')
        # print nac

        for ip in output:
            print '*********',ip
            if ip[0] in not_exist_lst:
                self.assertRaisesRegexp(WtWhoisException, 'o root WHOIS server found for domain.', ws.search_whois, '0.0.0.1')
                print "Not exists"
            else:
                nac = ws.search_whois(ip[0])
                # print nac
                # print output[ip]
                self.assertListEqual(nac, output[ip])

    def test_find_whois(self):
        db = DbManager()
        db.connect()
        try:
            db.clear_db()
        finally:
            db.close()

        for i, ip in enumerate(output):
            if ip[0] not in not_exist_lst:
                dt = datetime.now()
                find_whois(ip[0], 'www.referer.url.%i' % i, 'www.page.url.%i' % i, dt)

        db.connect()
        try:
            cur = db.conn.cursor()
            cur.execute("""SELECT * FROM wt_visitor;""")
            # rs = cur.fetchall()
            rsd = dict_fetchall(cur)
            for rowd in rsd:
                # print rowd['ip_id']
                cur.execute("""SELECT * FROM wt_ip WHERE id = %s;""", (rowd['ip_id'],))
                ip_rsd = dict_fetchall(cur)
                self.assertEqual(len(ip_rsd), 1)
                # print ip_rsd
                cur.execute("""SELECT * FROM wt_organization WHERE id = %s;""", (ip_rsd[0]['organization_id'],))
                organization_rsd = dict_fetchall(cur)
                self.assertEqual(len(organization_rsd), 1)


            cur.execute("""SELECT id FROM wt_organization;""")
            organization_rsd = dict_fetchall(cur)
            for rowd in organization_rsd:
                cur.execute("""SELECT id FROM wt_ip WHERE organization_id = %s;""", (rowd['id'],))
                ip_rsd = dict_fetchall(cur)
                self.assertTrue(len(ip_rsd) >= 1)
                for ip_rowd in ip_rsd:
                    cur.execute("""SELECT * FROM wt_visitor WHERE ip_id = %s;""", (ip_rowd['id'],))
                    org_rsd = dict_fetchall(cur)
                    self.assertTrue(len(org_rsd) >= 1)
        finally:
            db.close()

    def test_send_whois_message(self):
        e = WtWhoisException('Testing message service')
        ip_address = '0.0.0.0'
        page_url = 'testing.message.service'
        date_time_of_visit = datetime.now()
        send_whois_message(e, ip_address, page_url, date_time_of_visit)

#[u'Internet Assigned Numbers Authority', [u'//www.iana.org.'], u'US']

if __name__ == '__main__':
#    unittest.main()

    lock_suite = unittest.TestSuite()
    lock_suite.addTest(TestLockUtils("test_lock"))
    runner = unittest.TextTestRunner()
    runner.run(lock_suite)
