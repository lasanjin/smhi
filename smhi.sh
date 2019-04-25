#!/bin/bash

smhi() {
    if ! is_valid $1; then
        echo -e "\nInvalid input\n"
        return 0
    fi

    if ! is_zipcode $2 && ! is_empty $2; then
        echo -e "\nInvalid input\n"
        return 0
    fi

    local zurl=$(zipcode_url $2)
    local zipcoords=$(zipcode_coords $zurl)
    local coords=$(coordinates $2 ${zipcoords[@]})

    if ! is_coords ${coords[@]}; then
        echo -e "\nInvalid zipcode\n"
        return 0
    fi

    local surl=$(smhi_url ${coords[@]})
    read -r -a forecast -d '' <<<"$(smhi_data $surl)"
    currentdir
    style

    local today=$(date +'%Y-%m-%d')
    local todate=$(date -d "$today+$1 days" +'%s')
    local tmpdate
    local tmpdesc
    local symbol
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
            local units='\t°C\tm/s\tmm\h\tsymb\tdesc'
            local lang='sv_SE.utf-8'
            local day=$(LC_TIME=$lang date --date "$validTime" +'%A')

            echo -e "\n${bold}${green}${day}${default}${units}"

            tmpdate=$date
            tmpdesc=" "
        fi

        local description=$(sed "${Wsymb2}q;d" $dir/Wsymb2SV.txt)
        if ! equals "$description" "$tmpdesc"; then
            tmpdesc=$description
        else
            description="^"
        fi

        local symbol=$(sed "${Wsymb2}q;d" $dir/symbols.txt)
        local time=$(date --date "$validTime" '+%H:%M')
        local head=${dim}$time'\t'${default}${bold}
        local tail='\t'${blue}${ws}'\t'${pmin}${default}${dim}'\t'${symbol}'\t'${description}${default}

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

coordinates() {
    local zipcode=$1 && shift
    local tmpcoords=($@)

    #default coords
    local -A coords=(
        [lat]=57.721920
        [long]=11.923514)

    if ! is_empty $zipcode; then
        coords[lat]=${tmpcoords[0]}
        coords[long]=${tmpcoords[1]}
    fi

    echo ${coords[@]}
}

zipcode_url() {
    local hostname='http://yourmoneyisnowmymoney.com/'
    local api='api/zipcodes/?zipcode='$1''
    local filename='?response=json'
    local zurl=''$hostname''$api''$filename''
    echo $zurl
}

zipcode_coords() {
    local data=$(curl -s $1 | jq -r '.results[] | .lat, .lng')
    declare -A local coords
    echo $data
}

smhi_url() {
    local smhicoords=($@)
    local lat='lat/'${smhicoords[0]}'/'
    local long='lon/'${smhicoords[1]}'/'
    local hostname='https://opendata-download-metfcst.smhi.se/'
    local api='api/category/pmp3g/version/2/geotype/point/'
    local filename='data.json'
    local surl=''$hostname''$api''$long''$lat''$filename''
    echo $surl
}

smhi_data() {
    local forecast=$(
        curl -s "$surl" | jq -r '.timeSeries[].parameters|=sort_by(.name) | 
    .timeSeries[] | .validTime, (.parameters[] | 
    select(.name == ("Wsymb2", "pmin", "t", "ws")) | .values[])'
    )
    echo ${forecast[@]}
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

is_coords() {
    local coords=($@)
    local wildcard=${coords[0]}
    is_float $wildcard
}

currentdir() {
    dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
}

temp() {
    [ 1 -eq $(echo "$2 >= $1" | bc) ]
}

equals() {
    [ "$1" == "$2" ]
}

is_float() {
    [[ $1 =~ ^[0-9]+\.?[0-9]+$ ]]
}

is_integer() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

is_empty() {
    [ -z "$1" ]
}

is_zipcode() {
    local input=$1
    is_integer $1 && [ ${#input} -eq 5 ]
}

is_valid() {
    is_integer $1 && ! [ $1 -lt 1 ] && ! [ $1 -gt 10 ]
}

smhi $1 $2
