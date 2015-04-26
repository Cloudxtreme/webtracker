#!/usr/bin/python
# -*- coding: utf-8 -*-
from MySQLdb import connect
import MySQLdb
from webtracker.settings import DB_PARMS
from whois_exception import WhoisDatabaseException


class DbManager():
    """
    The class inserts and updates whois information in the database
    """

    def __init__(self):
        self.conn = None

    def connect(self):
        self.conn = connect(**DB_PARMS)
        return self.conn

    def close(self, commit=True):
        if commit == True:
            self.conn.commit()
        elif commit == False:
            self.conn.rollback()
        elif commit is None:
            pass
        self.conn.close()

    def commit_changes(self, commit=True):
        if commit:
            self.conn.commit()
        else:
            self.conn.rollback()

    def append_new_org(self, org_name, org_address, country):
        """ if organization does not exists then append to table
        :param org_name: string
        :param org_address: list of strings
        :param country: string
        :return: organization id or None if organization was not append
        """
        if country is None:
            country = ''
        org_id = self.find_org(org_name, country)
        if org_id is None:
            new_org_id = self.append_org(org_name, org_address, country)
        else:
            new_org_id = org_id
            # TODO: update org address
        return new_org_id

    def append_org(self, org_name, org_address, country):
        """ append information about organization to database
        :param org_name: string
        :param org_address: list of strings
        :param country: string
        """

        cur = self.conn.cursor()
        if org_name is None:
            org_name = ''

        if country is None:
            country = ''
        # address = '; '.join(org_address)
        address = '|'.join(org_address)
        cur.execute("""INSERT INTO wt_organization
            (organization_name, country, organization_address)
            VALUES(%s, %s, %s);""",  (org_name, country, address,))

        cur.execute("""SELECT LAST_INSERT_ID();""")
        rs = cur.fetchall()
        org_id = rs[0][0]
        return org_id

    def find_org(self, org_name, country):
        conn_cursor = self.conn.cursor()
        cur = conn_cursor
        cur.execute("""SELECT id FROM wt_organization
                      WHERE organization_name = %s AND country = %s;""", (org_name, country,))
        rs = cur.fetchall()
        if len(rs) == 0:
            return None
        elif len(rs) == 1:
            return rs[0][0]
        else:
            raise MySQLdb.IntegrityError('Duplicate organization %s from country %s in table' % (org_name, country))

    def find_ip(self, ip_address, org_id):
        """ find specified ip_address in the visitors table and return organization id if exist
        :param ip_address: ip_address
        :return: ip id, organization id
        """

        cur = self.conn.cursor()
        if org_id is None:
            cur.execute("""SELECT id FROM wt_ip
              WHERE ip_address = %s AND organization_id IS NULL;""", (ip_address,))
        else:
            cur.execute("""SELECT id FROM wt_ip
              WHERE ip_address = %s AND organization_id = %s;""", (ip_address, org_id,))

        rs = cur.fetchall()
        if len(rs) == 0:
            return None
        elif len(rs) == 1:
            assert rs[0][0] is not None
            return rs[0][0]
        else:
            raise MySQLdb.IntegrityError("Duplicate ip address %s for one organization %s" % (ip_address, org_id))

    def append_new_ip(self, new_ip_address, new_org_id):
        ip_id = self.find_ip(new_ip_address, new_org_id)
        if ip_id is None:
            ip_id = self.append_ip(new_ip_address, new_org_id)
        return ip_id

    def append_ip(self, ip_address, org_id):
        cur = self.conn.cursor()
        cur.execute("""INSERT INTO wt_ip(organization_id, ip_address) VALUES(%s, %s);""",  (org_id, ip_address,))

        cur.execute("""SELECT LAST_INSERT_ID();""")
        rs = cur.fetchall()
        ip_id = rs[0][0]
        return ip_id

    def append_visitor(self, referer_url, page_url, datetime_of_visit, ip_id):
        """
        add visitor to visitors table
        """

        cur = self.conn.cursor()
        #ip_id = self.append_new_ip(visitor_ip, org_id)

        cur.execute(""" INSERT INTO wt_visitor(referer_url, page_url, datetime_of_visit, ip_id)
              VALUES(%s, %s, %s, %s);""", (referer_url, page_url, datetime_of_visit, ip_id,))

        cur.execute("""SELECT LAST_INSERT_ID();""")
        rs = cur.fetchall()
        vis_id = rs[0][0]
        return vis_id

    def clear_db(self, commit=True):
        cur = self.conn.cursor()
        cur.execute(""" delete from wt_visitor; """)
        cur.execute(""" delete from wt_ip; """)
        cur.execute(""" delete from wt_organization; """)
        if commit:
            self.conn.commit()

def dict_fetchall(cursor):
    """Returns all rows from a cursor as a dictionary pairs (field name, field value)
    """
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
