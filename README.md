# SMHI weather forecast CLI
Another project I did alongside my studies to learn some basic Python and Bash.

## Description
  + Outputs weather forecast data from SMHI API in terminal
  + Displays
    + ⏱️ Last time SMHI updated the forecast
    + 📍 Link to location on *Google Maps* and its coordinates
    + Data from API (customizable)
      + Temperature
      + Wind
      + Minimum rain
      + Description of weather
        + Matching symbol was added besides the API
  + Accepts parameters for specific location ( see [*How to run*](##How-to-run "Instructions") )
  + If coordinates are invalid, or if Google fails to find location, a default location (current location or location Gothenburg) is set

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
  -  input `a-z` `A-Z` `0-9`, default location is your location (or Gothenburg)


## [Linux](resources/README.md "Instructions for bash script")
Open link for instructions on how to run bash script [*smhi.sh*](smhi.sh "Source code")