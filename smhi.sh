#!/bin/bash

smhi() {
    local ndays=1
    if ! isempty $1; then
        ndays=$1

        if ! isdigit $1 || isnegative $1; then
            echo -e "\nInvalid input\n"
            return 0
        fi
    fi

    smhi_url
    smhi_data $url
    directory
    style

    read -r -a arr -d '' <<<"$data"

    local today=$(date +'%Y-%m-%d')
    local todate=$(date -d "$today+$ndays days" +'%s')
    local dir=$dir
    declare local tmpdate

    local length=${#arr[@]}
    for ((i = 0; i < $length; i += 5)); do

        local validTime=${arr[i]}

        local date=$(date --date "$validTime" +'%Y-%m-%d')
        local current=$(date -d "$date" +'%s')
        if [ $todate -le $current ]; then
            echo ""
            break
        fi

        local Wsymb2=${arr[$((i + 1))]}
        local pmin=${arr[$((i + 2))]}
        local t=${arr[$((i + 3))]}
        local ws=${arr[$((i + 4))]}

        if ! equals $date $tmpdate; then
            local units='\t°C\tm/s\tmm\h\tdesc'
            local lang='sv_SE.utf-8'
            local day=$(LC_TIME=$lang date --date "$validTime" +'%A')

            echo -e "\n${bold}${green}${day}${default}${units}"
            tmpdate=$date
        fi

        local time=$(date --date "$validTime" '+%H:%M')
        local description=$(sed "${Wsymb2}q;d" $dir/Wsymb2SV.txt)
        local head=${dim}$time'\t'${default}${bold}
        local tail='\t'${blue}${ws}'\t'${pmin}${default}${dim}'\t'${description}${default}

        if temp 30 $t; then
            echo -e "${head}${red}${t}${tail}"
        elif temp 25 $t; then
            echo -e "${head}${orange}${t}${tail}"
        elif temp 20 $t; then
            echo -e "${head}${yellow}${t}${tail}"
        else
            echo -e "${head}${blue}${t}${tail}"
        fi
    done
}

smhi_url() {
    local hostname='https://opendata-download-metfcst.smhi.se/'
    local api='api/category/pmp3g/version/2/geotype/point/'
    local long='lon/11.923514/'
    local lat='lat/57.721920/'
    local filename='data.json'
    url=''$hostname''$api''$long''$lat''$filename''
}

smhi_data() {
    data=$(
        curl -s $1 | jq -r '.timeSeries[].parameters|=sort_by(.name) | 
    .timeSeries[] | .validTime, (.parameters[] | 
    select(.name == ("Wsymb2", "pmin", "t", "ws")) | .values[])'
    )
}

style() {
    default='\e[0m'
    bold='\e[1m'
    green='\e[32m'
    blue='\e[94m'
    yellow='\e[33m'
    orange='\e[38;5;202m'
    red='\e[31m'
    dim='\e[2m'
}

directory() {
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
}

temp() {
    [ 1 -eq $(echo "$2 >= $1" | bc) ]
}

equals() {
    [ "$1" == "$2" ]
}

isdigit() {
    [[ "$1" =~ ^[0-9]*$ ]]
}

isnegative() {
    [ $1 -lt 0 ]
}

isempty() {
    [ -z $1 ]
}

smhi $1
