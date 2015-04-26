#!/usr/bin/python
# -*- coding: utf-8 -*-

from whois_tracker.parser import ParserManager
from db_manager import DbManager
from whois_tracker.whois_exception import WtWhoisException, WhoisParserException, UnknownWhoisServer, UnknownWhoisFormat
from messanger import send_whois_message
from MySQLdb import connect
from webtracker.settings import DB_PARMS
from db_manager import dict_fetchall
import sys


"""
use package http://cryto.net/pythonwhois/
pip install pythonwhois
"""


class WhoisTracker():
    def __init__(self):
        self.manager = ParserManager()

    def search_whois(self, ip_address):
        """retrieve whois information by ip_address address
        :param ip_address: string which contains ip address
        :return: list (org_name: string, org_address: list of string, country: string)
        """
        par_man = ParserManager()
        parser = par_man.create_parser(ip_address)
        parser.receive_raw_whois()
        nm_ad_cn = parser.parse()
        return nm_ad_cn


# def whois_handler(visitor_ip, referer_url, page_url, date_time_of_visit):
#     ws = WhoisTracker()
#     dbman = DbManager()
#     dbman.connect()
#     try:
#         try:
#             nac = ws.search_whois(visitor_ip)
#             assert nac is not None
#             nac_org_id = dbman.append_new_org(*nac)
#         except WhoisException as e:
#             send_whois_message(e, visitor_ip, page_url, date_time_of_visit)
#             nac_org_id = None
#             nac = None
#
#         ip_id = dbman.append_new_ip(visitor_ip, nac_org_id)
#         dbman.append_visitor(referer_url, page_url, date_time_of_visit, ip_id)
#     finally:
#         dbman.close()
#
#     return nac

def handle_whois(ws_tracker, db_man, visitor_ip, referer_url, page_url, datetime_of_visit):
    try:
        nac = ws_tracker.search_whois(visitor_ip)
        assert nac is not None
        nac_org_id = db_man.append_new_org(*nac)

    except WtWhoisException as e:
        send_whois_message(e, visitor_ip, page_url, datetime_of_visit)
        nac_org_id = None
        nac = None
    # except:
    #     print "Unexpected error:", sys.exc_info()[0]
    #     pass
    ip_id = db_man.append_new_ip(visitor_ip, nac_org_id)
    db_man.append_visitor(referer_url, page_url, datetime_of_visit, ip_id)

    return nac


def handle_whois_queue():
    """
    read visitors from database table and look for whois info
    :return: nothing
    """
    if is_whois_locked():
        return False
    lock_whois(True)
    try:
        visitor_lst = read_queue()
        for visitor in visitor_lst:
            ws = WhoisTracker()
            dbman = DbManager()
            dbman.connect()
            try:
                handle_whois(ws,
                             dbman,
                             visitor_ip=visitor['visitor_ip'],
                             referer_url=visitor['referer_url'],
                             page_url=visitor['page_url'],
                             datetime_of_visit=visitor['datetime_of_visit']
                )
                del_visitor_from_queue(visitor['id'], dbman.conn)
                dbman.commit_changes(True)
            except:
                dbman.commit_changes(False)
                raise
            finally:
                dbman.close(commit=None)
    finally:
        lock_whois(False)

    return True


def read_queue():
    conn = connect(**DB_PARMS)
    try:
        cur = conn.cursor()
        cur.execute("""SELECT id, visitor_ip, referer_url, page_url, datetime_of_visit
                        FROM wt_visitor_queue ORDER BY datetime_of_visit;
                    """)
        rs_dic = dict_fetchall(cur)

    finally:
        conn.close()

    return rs_dic


def lock_whois(lock_on):
    conn = connect(**DB_PARMS)
    try:
        cur = conn.cursor()
        cur.execute(""" update wt_queue_lock set lock_on = %s where id = 1; """, (lock_on,))
        conn.commit()
    finally:
        conn.close()


def is_whois_locked():
    conn = connect(**DB_PARMS)
    try:
        cur = conn.cursor()
        cur.execute(""" select lock_on from wt_queue_lock where id = 1; """)
        rec = cur.fetchone()
        locked = rec[0]
    finally:
        conn.close()
    return bool(locked)


def del_visitor_from_queue(visitor_id, conn):
    cur = conn.cursor()
    cur.execute("""DELETE FROM wt_visitor_queue WHERE id=%s;""", (visitor_id,))


if __name__ == '__main__':
    handle_whois_queue()
