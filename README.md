## Description
  + Outputs weather forecast data from SMHI API in terminal
  + Displays
    + ⏱️ Last time SMHI updated the forecast
    + 📍 Link to location on *Google Maps* and its coordinates
  + Obtains following data from API
    + Temperature
    + Wind
    + Minimum rain
    + Description of weather
      + Matching symbol was added besides the API
  + Accepts parameters for specific location ( see [*How to run*](##How-to-run "Instructions") )
  + If coordinates are invalid, or if Google fails to find location, a default location (current location or Gothenburg) is set

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

- `$@` 
  -  *optional*
  -  requires `$1`
  -  location
     -  example
        -  *Göteborg*
        -  *Chalmersplatsen 4*
        -  *Kiruna centrum*
        -  *Stockholm Karl XII:s torg*
  -  input `a-z` `A-Z` `0-9`, default location is your location (or Gothenburg)


## [Linux](resources/README.md "Instructions for bash script")
Open link for instructions on how to run bash script [*smhi.sh*](smhi.sh "Source code")