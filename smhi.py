#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
import linecache
import collections
import urllib2
import locale
import json
import sys

locations = {"Lundby": (11.932365, 57.715626),
             "Chalmers": (11.973600, 57.689701)}

parameters = collections.OrderedDict(
    {"validTime": None, "t": None, "ws": None, "pmin": None, "Wsymb2": None})


def forecast():
    set_locale("sv_SE.utf-8")
    num_of_days = get_param()
    end_date = get_date(num_of_days)
    reference_time, forecast = get_data("Lundby")

    print "\n" + reference_time + style.DIM + " (last updated)" + style.DEFAULT
    print_data(forecast, end_date)
    print


def get_data(dest):
    rawdata = json.loads(urllib2.urlopen(
        'https://opendata-download-metfcst.smhi.se/'
        'api/category/pmp3g/version/2/geotype/point/'
        'lon/' + str(locations[dest][0]) + '/'
        'lat/' + str(locations[dest][1]) + '/'
        'data.json'
    ).read())

    time = rawdata['referenceTime']
    reference_time = format_time(time, '%y-%m-%d %H:%M')

    data = []
    for timestamp in rawdata['timeSeries']:
        values = parameters.copy()
        data.append(values)

        time = timestamp['validTime']
        values["validTime"] = format_time(time, '%y-%m-%d;%H')

        for parameter in timestamp['parameters']:

            if values.has_key(parameter['name']):
                values[str(parameter['name'])] = parameter['values'][0]

    return reference_time, data


def get_date(num_of_days):
    today = datetime.today()
    return (today + timedelta(days=num_of_days)).strftime('%y-%m-%d')


def format_time(time, format):
    return datetime.strptime(
        time, '%Y-%m-%dT%H:%M:%SZ').strftime(format)


def format_date(date):
    return datetime.strptime(date, '%y-%m-%d').strftime('%a')


def split_timestamp(timestamp):
    ts = timestamp["validTime"].split(";")
    date = ts[0]
    time = ts[1]
    return date, time


def print_header(date):
    units = "\t°C\t m/s\t mm\h\t symb\tdesc"
    lines = style.DIM + "-"*44 + style.DEFAULT

    print "\n" + lines
    print style.BOLD + style.GREEN + format_date(date) + style.DEFAULT + units
    print lines

    return date


def print_wsymb(tmp_desc, wsymb):
    print wsymb[0] + "\t",
    desc = wsymb[1].strip()

    if tmp_desc != desc:
        print style.DIM + desc + style.DEFAULT,
    else:
        print style.DIM + "↓" + style.DEFAULT,

    return desc


def print_parameters(timestamp, time, tmp_desc):
    print style.DIM + time + "\t" + style.DEFAULT,

    for key in ["t", "ws", "pmin"]:
        print style.BLUE + str(timestamp[key]) + "\t" + style.DEFAULT,

    wsymb = linecache.getline(
        'resources/Wsymb2SV.txt', timestamp["Wsymb2"]).split(",")
    tmp_desc = print_wsymb(tmp_desc, wsymb)

    print
    return tmp_desc


def print_data(forecast, end_date):
    tmp_date = None
    tmp_desc = None

    for timestamp in forecast:
        date, time = split_timestamp(timestamp)

        if date == end_date:
            return

        if date != tmp_date:
            tmp_date = print_header(date)

        tmp_desc = print_parameters(timestamp, time, tmp_desc)


def set_locale(code):
    locale.setlocale(locale.LC_ALL, code)


def is_int(param):
    try:
        int(param)
        return True
    except ValueError:
        return False


def get_param():
    try:
        param = sys.argv[1:][0]
        if is_int(param):
            if 0 < param:
                return int(param)
        return 0
    except IndexError:
        return 0


class style():
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = "\033[1m"
    DIM = '\033[2m'


forecast()
