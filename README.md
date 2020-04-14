# SMHI weather forecast CLI
Outputs SMHI weather forecast or warnings in terminal. Runs with Python 2, 3+.

## Description
  + Outputs weather forecast data from SMHI API in terminal
  + Displays
    + Ref time: Last time SMHI updated the forecast
    + Location: Coordinates and link to Google Maps
    + Data from API (customizable)
      + Temperature
      + Wind
      + Min rain
      + Humidity
      + Visibility
      + Thunder
      + Weather desc.
        + Matching symbols was added besides the API
  + Accepts parameters for specific location ( see [*How to run*](##How-to-run "Instructions") )
    + If Google fails to find location, current or default location (Gothenburg) is set

<img src="resources/smhi-py.gif" width="500">

## Install
```
$ curl "https://raw.githubusercontent.com/lasanjin/smhi-cli/master/install.sh" | bash
```

## How to run
```
$ smhi $1 $@
```

- `$1` 
  -  *optional*
  -  forecast (number of days)
     -  input `0-9`, default is today's weather
  -  warnings
     -  input `-w` to show all weather warnings from API

- `$@` 
  -  *optional*
  -  requires `$1` (does not work with `-w`)
  -  location
     -  example
        -  *Göteborg*
        -  *Chalmersplatsen 4*
        -  *Kiruna centrum*
        -  *Stockholm Karl XII:s torg*
  -  input `a-z` `A-Z` `0-9`, default location is current location (or Gothenburg)


## [Linux](resources/README.md "Instructions for bash script")
Open link for instructions on how to run bash script [*smhi.sh*](smhi.sh "Source code")
