#!/bin/bash

main() {
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
    #osx
    if [[ "$OSTYPE" == "darwin"* ]]; then
        JQ="$dir/resources/jq-osx-amd64"
    #linux
    else
        JQ="$dir/resources/jq-linux64"
    fi

    if ! is_valid $1; then
        echo -e "INVALID INPUT"
        return 0
    fi

    local desc_lang='Wsymb2SV.txt'
    local lang='sv_SE.utf-8'
    if equals $2 "en"; then
        desc_lang='Wsymb2EN.txt'
        lang='en_US.utf8'
    fi

    build_url
    read -r -a forecast -d '' <<<"$(get_data $URL)"
    # Get dir of script
    # Init colors
    DEFAULT='\e[0m'
    BOLD='\e[1m'
    GREEN='\e[32m'
    BLUE='\e[94m'
    YELLOW='\e[33m'
    ORANGE='\e[38;5;208m'
    RED='\e[31m'
    DIM='\e[2m'

    local units='\t°C\tm/s\tmm\h\tsymb\tdesc'
    local today=$(date +'%Y-%m-%d')
    local todate=$(date -d "$today+$1 days" +'%s')
    local tmpdate
    local tmpdesc
    local length=${#forecast[@]}

    for ((i = 0; i < $length; i += 5)); do
        local validTime=${forecast[i]}
        local date=$(date --date "$validTime" +'%Y-%m-%d')
        local current=$(date -d "$date" +'%s')

        if [ $todate -le $current ]; then
            echo ""
            break
        fi

        local Wsymb2=${forecast[$((i + 1))]}
        local pmin=${forecast[$((i + 2))]}
        local t=${forecast[$((i + 3))]}
        local ws=${forecast[$((i + 4))]}

        if ! equals $date $tmpdate; then
            local day=$(LC_TIME=$lang date --date "$validTime" +'%a')

            echo -e "\n${DIM} -------------------------------------------${DEFAULT}"
            echo -e " ${DEFAULT}${BOLD}${GREEN}${day}${DEFAULT}${units}"
            echo -e "${DIM} -------------------------------------------${DEFAULT}"

            tmpdate=$date
            tmpdesc=" "
        fi

        local desc=$(sed "${Wsymb2}q;d" $dir/resources/$desc_lang)
        local symbol=${desc%,*}

        if ! equals "$desc" "$tmpdesc"; then
            tmpdesc=$desc
        else
            desc="↓"
        fi

        local time=$(date --date "$validTime" '+%H')
        local head=' '${DIM}$time'\t'${DEFAULT}${BOLD}
        local tail='\t'${BLUE}${ws}'\t'${pmin}${DEFAULT}${DIM}'\t'${symbol}'\t'${desc##*,}${DEFAULT}

        if temp 30 $t; then
            echo -e "${head}${RED}${t}${tail}"
        elif temp 25 $t; then
            echo -e "${head}${ORANGE}${t}${tail}"
        elif temp 20 $t; then
            echo -e "${head}${YELLOW}${t}${tail}"
        else
            echo -e "${head}${BLUE}${t}${tail}"
        fi
    done
}

build_url() {
    IFS=',' read -r -a coords <<<"$(curl -s ipinfo.io | jq -r '.["loc"]')"
    unset IFS

    if ! is_empty ${coords[@]}; then
        local lat=${coords[0]}
        local long=${coords[1]}
    else
        local lat='57.715626'
        local long='11.932365'
    fi

    echo -e "LOCATION: $lat, $long"

    local hostname='https://opendata-download-metfcst.smhi.se/'
    local api='api/category/pmp3g/version/2/geotype/point/'
    local type='data.json'
    URL=''$hostname''$api'lon/'$long'/lat/'$lat'/'$type''
}

get_data() {
    local raw_data=$(
        curl -s "$URL" | $JQ -r '.timeSeries[].parameters|=sort_by(.name) | 
    .timeSeries[] | .validTime, (.parameters[] | 
    select(.name == ("Wsymb2", "pmin", "t", "ws")) | .values[])'
    )
    echo ${raw_data[@]}
}

temp() {
    [ 1 -eq $(echo "$2 >= $1" | bc) ]
}

equals() {
    [ "$1" == "$2" ]
}

is_integer() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

is_empty() {
    [ -z "$1" ]
}

is_valid() {
    is_integer $1 && ! [ $1 -lt 1 ] && ! [ $1 -gt 10 ]
}

main $1 $2
