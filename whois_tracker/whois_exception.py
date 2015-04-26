#!/usr/bin/python
# -*- coding: utf-8 -*-


class WtWhoisException(Exception):
    pass


class WhoisDatabaseException(WtWhoisException):
    pass


class WhoisParserException(WtWhoisException):
    pass


class UnknownWhoisServer(WhoisParserException):
    pass


class UnknownWhoisFormat(WhoisParserException):
    pass

