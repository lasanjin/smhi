#!/bin/bash

smhi() {
    if ! is_valid $1; then
        echo -e "Invalid input"
        return 0
    fi

    local desclang='Wsymb2SV.txt'
    local lang='sv_SE.utf-8'
    if equals $2 "en"; then
        desclang='Wsymb2EN.txt'
        lang='en_US.utf8'
    fi

    local surl=$(smhi_url)
    read -r -a forecast -d '' <<<"$(smhi_data $surl)"
    currentdir
    style

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

        local desc=$(sed "${Wsymb2}q;d" $dir/resources/$desclang)
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

smhi_url() {
    local lat='lat/57.715626/'
    local long='lon/11.932365/'
    local hostname='https://opendata-download-metfcst.smhi.se/'
    local api='api/category/pmp3g/version/2/geotype/point/'
    local filename='data.json'
    local surl=''$hostname''$api''$long''$lat''$filename''
    echo $surl
}

smhi_data() {
    local rawdata=$(
        curl -s "$surl" | jq -r '.timeSeries[].parameters|=sort_by(.name) | 
    .timeSeries[] | .validTime, (.parameters[] | 
    select(.name == ("Wsymb2", "pmin", "t", "ws")) | .values[])'
    )
    echo ${rawdata[@]}
}

style() {
    DEFAULT='\e[0m'
    BOLD='\e[1m'
    GREEN='\e[32m'
    BLUE='\e[94m'
    YELLOW='\e[33m'
    ORANGE='\e[38;5;208m'
    RED='\e[31m'
    DIM='\e[2m'
}

currentdir() { dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"; }

temp() { [ 1 -eq $(echo "$2 >= $1" | bc) ]; }

equals() { [ "$1" == "$2" ]; }

is_integer() { [[ "$1" =~ ^[0-9]+$ ]]; }

is_empty() { [ -z "$1" ]; }

is_valid() { is_integer $1 && ! [ $1 -lt 1 ] && ! [ $1 -gt 10 ]; }

smhi $1 $2
