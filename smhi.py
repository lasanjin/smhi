#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
import textwrap
import urllib2
import locale
import json
import sys
import re

locations = {"Gothenburg": ("11.986500", "57.696991"),
             "Chalmers": ("11.973600", "57.689701")}

parameters = {"validTime": None,  # ref time
              "t": None,  # temp
              "ws": None,  # wind
              "pmin": None,  # min rain
              "r": None,  # humidity
              "tstm": None,  # thunder
              "vis": None,  # visibility
              "Wsymb2": None}  # weather desc.

print_order = [
    ["Wsymb2", 'symb'],
    ["t", '°C'],
    ["ws", 'm/s'],
    ["pmin", 'mm\h'],
    ["r", '%h'],
    ["vis", 'km'],
    ["tstm", '%t']]


def main():
    set_locale("sv_SE.utf-8")
    coords = get_location()
    reference_time, forecast = get_forecast(coords)
    print_data(reference_time, coords, forecast)


def get_location():
    params = get_params()
    rawdata = get_gmaps_response(params)

    if rawdata == None:
        return constant.DEFAULT_COORDS

    coords = get_coords(rawdata)

    return coords


def get_gmaps_response(params):
    path = ""
    for param in params:
        path += param + constant.PLUS

    url = api.GMAPS_URL + urllib2.quote(path)

    return request(url)


def get_coords(rawdata):
    coords = []
    for param in ["lon", "lat"]:
        match = find_coord(rawdata, param)
        index = get_index(match)

        if index == None:
            return constant.DEFAULT_COORDS

        length = index + 9
        wildcard = rawdata[index:length]
        c = to_float(wildcard)
        coord = str(c)

        if isinstance(c, float) and 7 <= len(coord) <= 9:
            coords.append(coord)
        else:
            return constant.DEFAULT_COORDS

    return coords


def find_coord(rawdata, coord):
    reg = {"lat": '(?<![0-9])[5-6][0-9]\.\d+',
           "lon": '(?<![0-9])[1-2][0-9]\.\d+'}

    return re.search(r''+reg[coord], rawdata)


def get_forecast(coords):
    url = api.SMHI_URL(coords[0], coords[1])
    res = request(url)

    if res == None:
        res = get_data(constant.DEFAULT_COORDS)

    rawdata = json.loads(res)
    return parse_data(rawdata)


def parse_data(rawdata):
    time = rawdata['referenceTime']
    reference_time = format_time(time, '%H:%M')

    forecast = []
    for timestamp in rawdata['timeSeries']:
        values = parameters.copy()
        forecast.append(values)
        time = timestamp['validTime']
        values["validTime"] = format_time(time, '%y-%m-%d;%H')

        for parameter in timestamp['parameters']:
            key = parameter['name']

            if values.has_key(key):
                values[key] = parameter['values'][0]

    return reference_time, forecast


def get_warnings():
    res = request(api.WARNINGS_URL)
    if res == None:
        return constant.NO_WARNING

    data = json.loads(res)
    warnings = data['message']['text']

    return warnings


def request(url):
    try:
        return urllib2.urlopen(url).read()

    except urllib2.HTTPError as e:
        print "HTTPError: {}, {}".format(e.code, e.reason)

    except urllib2.HTTPException as e:
        print "HTTPException: {}".format(e)

    except Exception as e:
        print "Exception: {}".format(e)


def get_index(match):
    try:
        return match.start()
    except AttributeError:
        return None


def to_date(num_of_days):
    today = datetime.today()
    return (today +
            timedelta(days=num_of_days)).strftime('%y-%m-%d')


def to_float(param):
    try:
        return float(param)
    except ValueError:
        return 1


def get_time_interval():
    try:
        param = sys.argv[1:][0]
        if param == constant.WARNING:
            print_warnings(get_warnings())
            quit()

        interval = int(param)
        return interval if interval > 0 and interval < 11 else 1

    except IndexError:
        return 1

    except ValueError:
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


def print_data(reference_time, coords, forecast):
    num_of_days = get_time_interval()
    end_date = to_date(num_of_days)

    print
    print_reference_time(reference_time)
    print_coords(coords)
    print_forecast(forecast, end_date)
    print


def print_coords(coords):
    if coords in locations.values():
        print constant.DIM + constant.LOCATION + constant.DEFAULT \
            + constant.NOT_FOUND + constant.DIM \
            + constant.DEFAULT_LOCATION + constant.DEFAULT
    else:
        cs = str(coords[1]) + ", " + str(coords[0])

        # hyperlink
        print \
            constant.DIM + constant.LOCATION + constant.DEFAULT + \
            constant.PREFIX + api.GMAPS_URL + cs + constant.POSTFIX(cs)


def print_reference_time(reference_time):
    print constant.DIM + constant.TIME + constant.DEFAULT + \
        reference_time


def get_units():
    units = ""

    for u in print_order:
        units += constant.TAB + u[1]

    units += constant.TAB + 'desc'

    return units


def get_lines(units):
    return constant.DIM + constant.LINE * \
        len(units.expandtabs()) + constant.DEFAULT


def print_header(date):
    units = get_units()
    lines = get_lines(units)

    print "\n" + lines
    print constant.BOLD + constant.GREEN + format_date(date) \
        + constant.DEFAULT + units
    print lines

    return date


def print_desc(timestamp, tmp_desc):
    wsymb = get_wsymb(timestamp["Wsymb2"])
    desc = wsymb[1]

    if tmp_desc != desc:
        print constant.DIM + desc + constant.DEFAULT,
    else:
        print constant.DIM + constant.ARROW_DOWN + constant.DEFAULT,

    return desc


def print_parameters(timestamp, time, tmp_desc):
    for key in print_order:
        parameter = timestamp[key[0]]
        k = key[0]

        if k == "Wsymb2":
            symb = get_wsymb(parameter)[0]
            print symb + constant.TAB,

        elif is_hot(key[0], parameter):
            print constant.YELLOW + str(parameter) \
                + constant.DEFAULT + constant.TAB,

        else:
            print constant.BLUE + str(parameter) \
                + constant.DEFAULT + constant.TAB,

    tmp_desc = print_desc(timestamp, tmp_desc)
    print

    return tmp_desc


def is_hot(key, temp):
    return key == "t" and temp >= 25.0


def print_forecast(forecast, end_date):
    tmp_date = None
    tmp_desc = None

    for timestamp in forecast:
        date, time = split_timestamp(timestamp)

        if date == end_date:
            return

        if date != tmp_date:
            tmp_date = print_header(date)
            tmp_desc = None

        print constant.DIM + time + constant.TAB + constant.DEFAULT,
        tmp_desc = print_parameters(timestamp, time, tmp_desc)


def print_warnings(warnings):
    lines = get_lines(get_units())
    length = str(len(lines))

    print constant.NEWLINE + lines

    print('\n'.join(line for line in re.findall(
        r'.{1,' + re.escape(length) + '}(?:\s+|$)', warnings))) \
        .replace("\n\n", "\n")

    print lines + constant.NEWLINE


def set_locale(code):
    locale.setlocale(locale.LC_ALL, code)


class api:
    WARNINGS_URL = 'https://opendata-download-warnings.smhi.se/' \
        'api/version/2/messages.json'
    GMAPS_URL = 'https://www.google.com/maps/place/'
    BASE_URL = 'https://opendata-download-metfcst.smhi.se/' \
        'api/category/pmp3g/version/2/geotype/point/'

    @staticmethod
    def SMHI_URL(lon, lat):
        return api.BASE_URL + \
            'lon/' + lon + \
            '/lat/' + lat + \
            '/data.json'


class constant:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = "\033[1m"
    DIM = '\033[2m'
    TIME = 'Ref time: '  # '⏱️  '
    PIN = '📍 '
    ARROW_DOWN = "↓"
    LINE = "-"
    NOT_FOUND = 'not found'
    DEFAULT_LOCATION = ' (default Gothenburg)'
    LOCATION = 'Location: '
    TAB = '\t'
    PLUS = "+"
    NEWLINE = '\n'
    WARNING = '-w'
    NO_WARNING = 'Inga varningar'
    PREFIX = '\x1b]8;;'
    INVALID_URL = "\nInvalid url"
    DEFAULT_COORDS = locations["Gothenburg"]

    @staticmethod
    def POSTFIX(coords):
        return '//\a' + coords + constant.PREFIX + '\a'


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


if __name__ == "__main__":
    main()
