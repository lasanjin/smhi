## Description
Outputs weather forecast in terminal from SMHI api.

<img src="resources/smhi-GIF.gif" width="640">

## Get jq
Alt 1
1. Install jq
```
$ sudo apt-get install jq
```

Alt 2
1. Download jq
```
$ wget https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
```
2. Make script executable
```
$ sudo chmod +x ./jq-linux64.sh 
```
3. Replace `jq` with `./jq-linux64` in `expressen_data()` function


## How to run
1. Make script executable
```
$ sudo chmod +x ./smhi.sh 
```

2. Run script
```
$ ./smhi.sh $1 $2
```
- `$1` 
  -  *optional*
  -  forecast
     -  #days from today
        -  input `0-9`, default is today's weather

- `$2`
  -  *optional*
  -  Swedish zipcode
     -  input `xxxxx` and not `xxx xx`
        -  examples
           -  41296 *Chalmers*
           -  98131 *Kiruna*
        -  default are 41716 coordinates