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
    from urllib2 import quote
elif PY_VERSION >= 3:
    import urllib.request as urllib2
    from urllib.parse import quote


LOCATIONS = {'Gothenburg': ('11.986500', '57.696991'),
             'Chalmers': ('11.973600', '57.689701')}

PARAMETERS = {'validTime': None,  # ref time
              't': None,  # temp
              'ws': None,  # wind
              'pmin': None,  # min rain
              'r': None,  # humidity
              'tstm': None,  # thunder
              'vis': None,  # visibility
              'Wsymb2': None}  # weather desc.

PRINT_ORDER = [
    ['Wsymb2', 'symb'],
    ['t', '°C'],
    ['pmin', 'mm/h'],
    ['ws', 'm/s'],
    ['r', '%h'],
    ['vis', 'km'],
    ['tstm', '%t']]


def main():
    locale.setlocale(locale.LC_ALL, 'sv_SE.utf-8')
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

    info = Utils.style("[INFO]", [], "green")
    print(info, "FETCHING DATA...")

    coords = get_location()
    reference_time, forecast = get_forecast(coords)
    # print(json.dumps(forecast, indent=2, ensure_ascii=False))  # debug
    print_data(reference_time, coords, forecast, num_of_days)


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

    return Api.GMAPS_URL + quote(path)


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


def request(url):
    try:
        return urllib2.urlopen(url).read().decode('utf-8')
    except Exception as e:
        print('Exception:', e)


def format_time(time, format):
    return datetime.strptime(
        time, Utils.format('YmdHMSZ')).strftime(format)


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

    @staticmethod
    def style(output, color, styles=[]):
        if color is not None:
            output = {
                'green': '\033[92m%s',
                'blue': '\033[94m%s',
            }[color] % output

        for style in styles:
            output = {
                'bold': '\033[1m%s',
                'dim': '\033[2m%s'
            }[style] % output

        return output + '\033[0m'  # default

    @staticmethod
    def wsymb_icon(arg):
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


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(reference_time, coords, forecast, num_of_days):
    end_date = (
        datetime.today() + timedelta(days=num_of_days)) \
        .strftime(Utils.format('ymd'))

    print()
    # print reference time
    print(Utils.style('REF TIME:', ['dim']), reference_time)
    # print coords
    if coords in LOCATIONS.values():
        print(Utils.style('LOCATION:', ['dim']),
              'NOT FOUND',
              Utils.style(Utils.DEFAULT_LOCATION, ['dim']))
    else:
        cs = str(coords[1]) + ', ' + str(coords[0])
        # hyperlink
        print(Utils.style('LOCATION:', ['dim']),
              Utils.PREFIX + Api.GMAPS_URL + cs + Utils.postfix(cs))
    # print forecast
    print_forecast(forecast, end_date)
    print()


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

        print(Utils.style(time + '\t', ['dim']), end=' ')

        prev_desc = print_values(timestamp, prev_desc)


def print_header(date):
    header = build_header()
    line = Utils.style('-' * len(header.expandtabs()), ['dim'])
    day = datetime.strptime(date, Utils.format('ymd')).strftime('%a')

    print('\n' + line)
    print(Utils.style(day, ['bold'], 'green') + header)
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
            symb = Utils.wsymb_icon(value)[0]
            print(symb + '\t', end=' ')
        else:
            print(Utils.style(str(value), [], 'blue') + '\t', end=' ')

    prev_desc = print_desc(timestamp, prev_desc)
    print()

    return prev_desc


def print_desc(timestamp, prev_desc):
    wsymb = Utils.wsymb_icon(timestamp['Wsymb2'])
    desc = wsymb[1]

    if prev_desc != desc:
        print(Utils.style(desc, ['dim']), end=' ')
    else:
        print(Utils.style('↓', ['dim']), end=' ')

    return desc


def print_warnings(warnings):
    sep = build_separator(build_header())  # keep same length as header
    l = str(len(sep))

    print('\n' + sep)
    # pretty output
    print(('\n'.join(line for line in re.findall(
        r'.{1,' + re.escape(l) + '}(?:\s+|$)', warnings)))
        .replace('\n\n', '\n'))
    print(sep + '\n')


if __name__ == '__main__':
    main()
