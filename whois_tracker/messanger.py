#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib
import datetime
import logging

# see mailing samples by link:
# http://stackoverflow.com/questions/10147455/trying-to-send-email-gmail-as-mail-provider-using-python
# see mailing samples with attachments by link:
# http://www.jayrambhia.com/blog/send-emails-using-python/


LOG_FILENAME = 'webtracker.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class WhoisMessanger(object):
    def __init__(self, ip_address, server_url, port):
        self._ip_address = ip_address
        self._server_url = server_url
        self._port = port

    def send_message(self, msg):
        send_email(msg)


def send_whois_message(message, ip_address, page_url, date_time_of_visit):
    msg_text = 'e_msg = %s, ip_address = %s, page_url = %s, datetime of visit = %s' \
               % (message, ip_address, page_url, date_time_of_visit)
    send_email(msg_text)


def send_email(msg_text):
    gmail_user = "dashboard.messages@gmail.com"
    gmail_pwd = "draobhsad"
    FROM = 'webtracker'
    TO = ['freelancer.sergey@gmail.com'] #must be a list
    SUBJECT = "message from webtracker"
    TEXT = msg_text

    logging.debug(TEXT)

    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        logging.info('sent the message: %s' % msg_text)
        # print 'successfully sent the mail'
    except Exception:
        logging.critical("failed to send e-mail")


if __name__ == '__main__':
    pass
