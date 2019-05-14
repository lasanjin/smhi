## Description
  + Outputs weather forecast data from SMHI api in terminal
  + Accepts parameters for specific location ( see [*How to run*](##How-to-run "Instructions") )
  + If Google fails to find location a default location (current location or Gothenburg) is entered

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