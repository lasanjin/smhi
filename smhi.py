#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
import urllib2
import locale
import json
import sys
import re

locations = {"Gothenburg": ("11.986500", "57.696991"),
             "Chalmers": ("11.973600", "57.689701")}

parameters = {"validTime": None, "t": None,
              "ws": None, "pmin": None, "Wsymb2": None}


def forecast():
    set_locale("sv_SE.utf-8")

    num_of_days = get_time_interval()
    end_date = to_date(num_of_days)

    coords = search()
    reference_time, forecast = get_data(coords)

    print_coords(coords)
    print_reference_time(reference_time)
    print_data(forecast, end_date)
    print


def search():
    params = get_params()
    rawdata = gmaps_response(params)
    coords = get_coords(rawdata)

    return coords


def gmaps_response(params):
    url = 'https://www.google.com/maps/place/'
    for param in params:
        url += param + "+"

    return urllib2.urlopen(url).read()


def get_coords(rawdata):
    coords = []
    for param in ["lon", "lat"]:
        match = find_coord(rawdata, param)
        index = get_index(match)

        if index == None:
            return locations["Gothenburg"]

        length = index + 9
        wildcard = rawdata[index:length]
        c = to_float(wildcard)
        coord = str(c)

        if is_valid_coord(param, c, coord):
            coords.append(coord)
        else:
            return locations["Gothenburg"]

    return coords


def is_valid_coord(param, c, coord):
    if isinstance(c, float) and 7 <= len(coord) <= 9:
        if param == "lon":
            return 10.0 < c < 24.2
        elif param == "lat":
            return 55.2 < c < 69.0
    else:
        return False


def find_coord(rawdata, coord):
    reg = {"lat": '(?<![0-9])[5-6][0-9]\.\d+',
           "lon": '(?<![0-9])[1-2][0-9]\.\d+'}

    return re.search(r''+reg[coord], rawdata)


def get_data(coords):
    rawdata = json.loads(urllib2.urlopen(
        'https://opendata-download-metfcst.smhi.se/'
        'api/category/pmp3g/version/2/geotype/point/'
        'lon/' + coords[0] + '/'
        'lat/' + coords[1] + '/'
        'data.json'
    ).read())

    time = rawdata['referenceTime']
    reference_time = format_time(time, '%H:%M')

    data = []
    for timestamp in rawdata['timeSeries']:
        values = parameters.copy()
        data.append(values)
        time = timestamp['validTime']
        values["validTime"] = format_time(time, '%y-%m-%d;%H')

        for parameter in timestamp['parameters']:
            key = parameter['name']

            if values.has_key(key):
                values[key] = parameter['values'][0]

    return reference_time, data


def get_index(match):
    try:
        return match.start()
    except AttributeError:
        return None


def to_date(num_of_days):
    today = datetime.today()
    return (today +
            timedelta(days=num_of_days)).strftime('%y-%m-%d')


def to_int(param):
    try:
        return int(param)
    except ValueError:
        return 1


def to_float(param):
    try:
        return float(param)
    except ValueError:
        return 1


def get_time_interval():
    try:
        param = sys.argv[1:][0]
        interval = to_int(param)
        if 0 < interval:
            return interval

        return 1
    except IndexError:
        return 1


def get_params():
    try:
        return sys.argv[2:]
    except IndexError:
        return [""]


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


def print_coords(coords):
    print
    if coords[0] in locations.values():
        print style.PIN + "Location not found" + \
            style.DIM + " (default Gothenburg)" + style.DEFAULT
    else:
        link = 'https://www.google.com/maps/place/'
        cs = str(coords[1]) + ", " + str(coords[0])

        # hyperlink
        print style.PIN +  \
            '\x1b]8;;' + link + cs + '//\aLocation link\x1b]8;;\a' + \
            style.DIM + "      [" + cs + "]" + style.DEFAULT


def print_reference_time(reference_time):
    print style.TIME + reference_time + style.DIM + \
        style.TAB + style.UPDATE + style.DEFAULT


def print_header(date):
    lines = style.DIM + style.LINE*44 + style.DEFAULT
    units = \
        style.TAB + '°C' + \
        style.TAB + 'm/s' + \
        style.TAB + 'mm\h' + \
        style.TAB + 'symb' + \
        style.TAB + 'desc'

    print "\n" + lines
    print style.BOLD + style.GREEN + format_date(date) \
        + style.DEFAULT + units
    print lines

    return date


def print_wsymb(tmp_desc, wsymb):
    print wsymb[0] + style.TAB,
    desc = wsymb[1]

    if tmp_desc != desc:
        print style.DIM + desc + style.DEFAULT,
    else:
        print style.DIM + style.DOWN + style.DEFAULT,

    return desc


def print_parameters(timestamp, time, tmp_desc):
    for key in ["t", "ws", "pmin"]:
        print style.BLUE + str(timestamp[key]) \
            + style.DEFAULT + style.TAB,

    wsymb = get_wsymb(timestamp["Wsymb2"])
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
            tmp_desc = None

        print style.DIM + time + style.TAB + style.DEFAULT,
        tmp_desc = print_parameters(timestamp, time, tmp_desc)


def set_locale(code):
    locale.setlocale(locale.LC_ALL, code)


class style():
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = "\033[1m"
    DIM = '\033[2m'
    TIME = '⏱️  '
    PIN = '📍 '
    DOWN = "↓"
    LINE = "-"
    UPDATE = '      (Last updated)'
    TAB = '\t'


def get_wsymb(arg):
    return {
        1: ['☀️', 'Klart'],
        2: ['🌤️', 'Lätt molnighet'],
        3: ['⛅', 'Halvklart'],
        4: ['🌥️', 'Molnigt'],
        5: ['☁️', 'Mycket moln'],
        6: ['☁️', 'Mulet'],
        7: ['🌫', 'Dimma'],
        8: ['🌦️', 'Lätt regnskur'],
        9: ['🌦️', 'Regnskur'],
        10: ['🌦️', 'Kraftig regnskur'],
        11: ['⛈️', 'Åskväder'],
        12: ['🌨️', 'Lätt regnblandad snöby'],
        13: ['🌨️', 'Regnblandad snöby'],
        14: ['🌨️', 'Kraftig regnblandad snöby'],
        15: ['❄️', 'Lätt snöbyar'],
        16: ['❄️', 'Snöby'],
        17: ['❄️', 'Kraftig snöby'],
        18: ['🌧️', 'Lätt regn'],
        19: ['🌧️', 'Regn'],
        20: ['🌧️', 'Kraftigt regn'],
        21: ['🌩️', 'Åska'],
        22: ['🌨️', 'Lätt regnblandad snö'],
        23: ['🌨️', 'Regnblandad snö'],
        24: ['🌨️', 'Kraftig regnblandad snö'],
        25: ['❄️', 'Lätt snöfall'],
        26: ['❄️', 'Snöfall'],
        27: ['❄️', 'Kraftigt snöfall']
    }[arg]


forecast()
