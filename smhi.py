#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print python2
from datetime import datetime
from datetime import timedelta
import locale
import json
import sys
import re
import six

if six.PY2:  # python2
    import urllib2
    import httplib
elif six.PY3:  # python3
    import http.client as httplib  # httplib.HTTPException
    import urllib.error as urllib2  # urllib2.HTTPError
    import urllib.request
    import urllib.parse


locations = {'Gothenburg': ('11.986500', '57.696991'),
             'Chalmers': ('11.973600', '57.689701')}

parameters = {'validTime': None,  # ref time
              't': None,  # temp
              'ws': None,  # wind
              'pmin': None,  # min rain
              'r': None,  # humidity
              'tstm': None,  # thunder
              'vis': None,  # visibility
              'Wsymb2': None}  # weather desc.

print_order = [
    ['Wsymb2', 'symb'],
    ['t', '°C'],
    ['ws', 'm/s'],
    ['pmin', 'mm\h'],
    ['r', '%h'],
    ['vis', 'km'],
    ['tstm', '%t']]


def main():
    try:
        arg = sys.argv[1:][0]

        if arg == '-w':
            print_warnings(get_warnings())
            quit()

    except Exception:
        pass

    locale.setlocale(locale.LC_ALL, 'sv_SE.utf-8')
    coords = get_location()
    reference_time, forecast = get_forecast(coords)
    print_data(reference_time, coords, forecast)


# -----------------------------------------------------------------
# FIND COORDINATES
# -----------------------------------------------------------------
def get_location():
    try:
        location = sys.argv[2:]
    except IndexError:
        location = ''

    url = build_gmaps_request(location)
    response = request(url)

    if response == None:
        return C.DEFAULT_COORDS

    coords = find_coords(response)

    return coords


def build_gmaps_request(location):
    path = ''
    for l in location:
        path += l + '+'

    if six.PY2:
        url = api.GMAPS_URL + urllib2.quote(path)
    elif six.PY3:
        url = api.GMAPS_URL + urllib.parse.quote(path)

    return url


def find_coords(response):
    coords = []
    for coord in ['lon', 'lat']:
        match = re.search(r'' + C.REGEX[coord], response)

        try:
            index = match.start()
        except AttributeError:
            return C.DEFAULT_COORDS

        l = index + 9
        string = response[index:l]

        try:
            coord = float(string)
        except ValueError:
            coord = 1

        if isinstance(coord, float) and 7 <= len(str(coord)) <= 9:
            coords.append(str(coord))
        else:
            return C.DEFAULT_COORDS

    return coords


# -----------------------------------------------------------------
# GET FORECAST
# -----------------------------------------------------------------
def get_forecast(coords):
    url = api.url(coords[0], coords[1])
    response = request(url)

    if response == None:
        response = request(C.DEFAULT_COORDS)

    rawdata = json.loads(response)
    return parse_data(rawdata)


def parse_data(rawdata):
    time = rawdata['referenceTime']
    reference_time = format_time(time, C.format('HM'))
    forecast = []

    for timestamp in rawdata['timeSeries']:
        values = parameters.copy()
        forecast.append(values)
        time = timestamp['validTime']
        values['validTime'] = format_time(time, C.format('ymdH'))

        for parameter in timestamp['parameters']:
            key = parameter['name']

            if key in values:
                values[key] = parameter['values'][0]

    return reference_time, forecast


def get_warnings():
    res = request(api.WARNINGS_URL)

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
        if six.PY2:
            return urllib2.urlopen(url).read()
        elif six.PY3:
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
        time, C.format('YmdHMSZ')).strftime(format)


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(reference_time, coords, forecast):
    try:
        interval = int(sys.argv[1:][0])
        num_of_days = interval if interval > 0 and interval < 11 else 1
    except Exception:
        num_of_days = 1

    end_date = (datetime.today() + timedelta(days=num_of_days)) \
        .strftime(C.format('ymd'))

    print()
    print_reference_time(reference_time)
    print_coords(coords)
    print_forecast(forecast, end_date)
    print()


def print_coords(coords):
    # if coords in locations.values():
    if coords in list(locations.values()):
        print(color.dim('LOCATION:'),
              'NOT FOUND',
              color.dim(C.DEFAULT_LOCATION))
    else:
        cs = str(coords[1]) + ', ' + str(coords[0])
        # hyperlink
        print(color.dim('LOCATION:'),
              C.PREFIX + api.GMAPS_URL + cs + C.postfix(cs))


def print_reference_time(reference_time):
    print(color.dim('REF TIME:'), reference_time)


def print_header(date):
    header = build_header()
    sep = build_separator(header)
    day = datetime.strptime(date, C.format('ymd')).strftime('%a')

    print('\n' + sep)
    print(color.BOLD + color.green(day) + header)
    print(sep)


def build_header():
    header = ''
    for unit in print_order:
        header += '\t' + unit[1]

    header += '\tdesc'

    return header


def build_separator(header):
    line = '-' * len(header.expandtabs())
    return color.dim(line)


def print_values(timestamp, prev_desc):
    for parameter in print_order:
        value = timestamp[parameter[0]]

        if parameter[0] == 'Wsymb2':
            symb = get_wsymb_icon(value)[0]
            print(symb + '\t', end=' ')

        elif parameter[0] == 't' and value >= 40.0:
            print(color.red(str(value)) + '\t', end=' ')

        elif parameter[0] == 't' and value >= 30.0:
            print(color.orange(str(value)) + '\t', end=' ')

        elif parameter[0] == 't' and value >= 25.0:
            print(color.yellow(str(value)) + '\t', end=' ')

        else:
            print(color.blue(str(value)) + '\t', end=' ')

    prev_desc = print_desc(timestamp, prev_desc)
    print()

    return prev_desc


def print_desc(timestamp, prev_desc):
    wsymb = get_wsymb_icon(timestamp['Wsymb2'])
    desc = wsymb[1]

    if prev_desc != desc:
        print(color.dim(desc), end=' ')
    else:
        print(color.dim('↓'), end=' ')

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

        print(color.dim(time + '\t'), end=' ')
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
class api:
    GMAPS_URL = 'https://www.google.com/maps/place/'
    WARNINGS_URL = 'https://opendata-download-warnings.smhi.se/' \
        'api/version/2/messages.json'
    BASE_URL = 'https://opendata-download-metfcst.smhi.se/' \
        'api/category/pmp3g/version/2/geotype/point/'

    @staticmethod
    def url(lon, lat):
        return api.BASE_URL + \
            'lon/' + lon + \
            '/lat/' + lat + \
            '/data.json'


class C:
    DEFAULT_LOCATION = 'Gothenburg'
    DEFAULT_COORDS = locations[DEFAULT_LOCATION]
    PREFIX = '\x1b]8;;'
    REGEX = {'lat': '(?<![0-9])[5-6][0-9]\.\d+',
             'lon': '(?<![0-9])[1-2][0-9]\.\d+'}

    @staticmethod
    def postfix(coords):
        return '/\a' + coords + C.PREFIX + '\a'

    @staticmethod
    def format(arg):
        return {
            'HM': '%H:%M',
            'ymd': '%y-%m-%d',
            'ymdH': '%y-%m-%d;%H',
            'YmdHMSZ': '%Y-%m-%dT%H:%M:%SZ'
        }[arg]


class color:
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
        return color.DIM + output + color.DEFAULT

    @staticmethod
    def green(output):
        return color.GREEN + output + color.DEFAULT

    @staticmethod
    def blue(output):
        return color.BLUE + output + color.DEFAULT

    @staticmethod
    def yellow(output):
        return color.YELLOW + output + color.DEFAULT

    @staticmethod
    def red(output):
        return color.RED + output + color.DEFAULT

    @staticmethod
    def orange(output):
        return color.ORANGE + output + color.DEFAULT


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
