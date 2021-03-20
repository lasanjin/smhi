#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # python2 print
from datetime import datetime
from datetime import timedelta
import locale
import json
import sys
import re

PY_VERSION = sys.version_info[0]

if PY_VERSION < 3:
    import urllib2
    import httplib
elif PY_VERSION >= 3:
    import http.client as httplib  # httplib.HTTPException
    import urllib.error as urllib2  # urllib2.HTTPError
    import urllib.request
    import urllib.parse


LOCATIONS = {'Gothenburg': ('11.986500', '57.696991'),
             'Chalmers': ('11.973600', '57.689701')}

PARAMETERS = {'validTime': None,  # ref time
              't': None,  # temp
              'ws': None,  # wind
              'pmin': None,  # min rain
              'r': None,  # humidity
              'tstm': None,  # thunder
              'vis': None,  # visibility
              'Wsymb2': None}  # weather desUtils.

PRINT_ORDER = [
    ['Wsymb2', 'symb'],
    ['t', '°C'],
    ['pmin', 'mm/h'],
    ['ws', 'm/s'],
    ['r', '%h'],
    ['vis', 'km'],
    ['tstm', '%t']]


def main():
    try:
        interval = int(sys.argv[1:][0])
        num_of_days = interval if interval > 0 and interval < 11 else 1
        arg = sys.argv[1:][0]
        if arg == '-h':
            print('smhi [0-9 | -w] [LOCATION]')
        elif arg == '-w':
            print_warnings(get_warnings())
            quit()
    except Exception:
        num_of_days = 1
        pass

    locale.setlocale(locale.LC_ALL, 'sv_SE.utf-8')
    coords = get_location()
    reference_time, forecast = get_forecast(coords)
    print_data(reference_time, coords, forecast, num_of_days)


# -----------------------------------------------------------------
# FIND COORDINATES
# -----------------------------------------------------------------
def get_location():
    try:
        location = sys.argv[2:]
    except IndexError:
        location = ''

    url = build_gmaps_request(location)
    resp = request(url)

    if resp == None:
        return Utils.DEFAULT_COORDS

    coords = find_coords(resp)

    return coords


def build_gmaps_request(location):
    path = ''
    for l in location:
        path += l + '+'

    if PY_VERSION < 3:
        url = Api.GMAPS_URL + urllib2.quote(path)
    elif PY_VERSION >= 3:
        url = Api.GMAPS_URL + urllib.parse.quote(path)

    return url


def find_coords(response):
    coords = []
    for coord in ['lon', 'lat']:
        match = re.search(r'' + Utils.REGEX[coord], response)

        try:
            index = match.start()
        except AttributeError:
            return Utils.DEFAULT_COORDS

        l = index + 9
        string = response[index:l]

        try:
            coord = float(string)
        except ValueError:
            coord = 1

        if isinstance(coord, float) and 7 <= len(str(coord)) <= 9:
            coords.append(str(coord))
        else:
            return Utils.DEFAULT_COORDS

    return coords


# -----------------------------------------------------------------
# GET FORECAST
# -----------------------------------------------------------------
def get_forecast(coords):
    url = Api.url(coords[0], coords[1])
    resp = request(url)

    if resp == None:
        resp = request(Utils.DEFAULT_COORDS)

    json_data = json.loads(resp)
    # print(json.dumps(json_data, indent=2, ensure_ascii=False))  # debug

    return parse_data(json_data)


def parse_data(json_data):
    time = json_data['referenceTime']
    reference_time = format_time(time, Utils.format('HM'))
    forecast = []

    for timestamp in json_data['timeSeries']:
        values = PARAMETERS.copy()
        forecast.append(values)
        time = timestamp['validTime']
        values['validTime'] = format_time(time, Utils.format('ymdH'))

        for parameter in timestamp['parameters']:
            key = parameter['name']

            if key in values:
                values[key] = parameter['values'][0]

    return reference_time, forecast


def get_warnings():
    res = request(Api.WARNINGS_URL)

    if res == None:
        return 'INGA VARNINGAR'

    data = json.loads(res)
    warnings = data['message']['text']

    return warnings


# -----------------------------------------------------------------
# HELP FUNCTIONS
# -----------------------------------------------------------------
def request(url):
    try:
        if PY_VERSION < 3:
            return urllib2.urlopen(url).read()
        elif PY_VERSION >= 3:
            return urllib.request.urlopen(url).read().decode('utf-8')

    except urllib.error.HTTPError as e:
        print('HTTPError:', e.code)

    except urllib.error.URLError as e:
        print('URLError:', e.reason)

    except http.client.HTTPException as e:
        print('HTTPException:', e)

    except Exception as e:
        print('Exception:', e)


def format_time(time, format):
    return datetime.strptime(
        time, Utils.format('YmdHMSZ')).strftime(format)


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(reference_time, coords, forecast, num_of_days):
    end_date = (datetime.today() + timedelta(days=num_of_days)) \
        .strftime(Utils.format('ymd'))

    print()
    print_reference_time(reference_time)
    print_coords(coords)
    print_forecast(forecast, end_date)
    print()


def print_coords(coords):
    if coords in LOCATIONS.values():
        print(Style.dim('LOCATION:'),
              'NOT FOUND',
              Style.dim(Utils.DEFAULT_LOCATION))
    else:
        cs = str(coords[1]) + ', ' + str(coords[0])
        # hyperlink
        print(Style.dim('LOCATION:'),
              Utils.PREFIX + Api.GMAPS_URL + cs + Utils.postfix(cs))


def print_reference_time(reference_time):
    print(Style.dim('REF TIME:'), reference_time)


def print_header(date):
    header = build_header()
    line = Style.dim('-' * len(header.expandtabs()))
    day = datetime.strptime(date, Utils.format('ymd')).strftime('%a')

    print('\n' + line)
    print(Style.BOLD + Style.green(day) + header)
    print(line)


def build_header():
    header = ''
    for unit in PRINT_ORDER:
        header += '\t' + unit[1]
    header += '\tdesc'

    return header


def print_values(timestamp, prev_desc):
    for parameter in PRINT_ORDER:
        value = timestamp[parameter[0]]

        if parameter[0] == 'Wsymb2':
            symb = get_wsymb_icon(value)[0]
            print(symb + '\t', end=' ')
        else:
            print(Style.blue(str(value)) + '\t', end=' ')

    prev_desc = print_desc(timestamp, prev_desc)
    print()

    return prev_desc


def print_desc(timestamp, prev_desc):
    wsymb = get_wsymb_icon(timestamp['Wsymb2'])
    desc = wsymb[1]

    if prev_desc != desc:
        print(Style.dim(desc), end=' ')
    else:
        print(Style.dim('↓'), end=' ')

    return desc


def print_forecast(forecast, end_date):
    prev_date = None
    prev_desc = None

    for timestamp in forecast:
        ts = timestamp['validTime'].split(';')
        date, time = ts[0], ts[1]

        if date == end_date:
            return

        if date != prev_date:
            print_header(date)
            prev_date = date
            prev_desc = None

        print(Style.dim(time + '\t'), end=' ')
        prev_desc = print_values(timestamp, prev_desc)


def print_warnings(warnings):
    sep = build_separator(build_header())  # keep same length as header
    l = str(len(sep))

    print('\n' + sep)
    # pretty output
    print(('\n'.join(line for line in re.findall(
        r'.{1,' + re.escape(l) + '}(?:\s+|$)', warnings)))
        .replace('\n\n', '\n'))
    print(sep + '\n')


# -----------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------
class Api:
    GMAPS_URL = 'https://www.google.com/maps/place/'
    WARNINGS_URL = 'https://opendata-download-warnings.smhi.se/' \
        'api/version/2/messages.json'
    BASE_URL = 'https://opendata-download-metfcst.smhi.se/' \
        'api/category/pmp3g/version/2/geotype/point/'

    @staticmethod
    def url(lon, lat):
        return Api.BASE_URL + \
            'lon/' + lon + \
            '/lat/' + lat + \
            '/data.json'


class Utils:
    DEFAULT_LOCATION = 'Gothenburg'
    DEFAULT_COORDS = LOCATIONS[DEFAULT_LOCATION]
    PREFIX = '\x1b]8;;'
    REGEX = {'lat': '(?<![0-9])[5-6][0-9]\.\d+',
             'lon': '(?<![0-9])[1-2][0-9]\.\d+'}

    @staticmethod
    def postfix(coords):
        return '/\a' + coords + Utils.PREFIX + '\a'

    @staticmethod
    def format(arg):
        return {
            'HM': '%H:%M',
            'ymd': '%y-%m-%d',
            'ymdH': '%y-%m-%d;%H',
            'YmdHMSZ': '%Y-%m-%dT%H:%M:%SZ'
        }[arg]


class Style:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    ORANGE = '\033[38;5;202m'

    @staticmethod
    def dim(output):
        return Style.DIM + output + Style.DEFAULT

    @staticmethod
    def green(output):
        return Style.GREEN + output + Style.DEFAULT

    @staticmethod
    def blue(output):
        return Style.BLUE + output + Style.DEFAULT


def get_wsymb_icon(arg):
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


if __name__ == '__main__':
    main()
