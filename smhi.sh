#!/bin/bash

smhi() {
    smhi_url
    smhi_data $url

    read -r -a arr -d '' <<<"$data"

    style
    local length=${#arr[@]}
    local temp=''
    for ((i = 0; i < $length; i += 4)); do

        local validTime=${arr[i]}
        local pmin=${arr[$((i + 1))]}
        local t=${arr[$((i + 2))]}
        local ws=${arr[$((i + 3))]}

        local date=$(date --date "$validTime" +'%Y-%m-%d')

        if [ "$date" != "$temp" ]; then
            local units='\t°C\tm/s\tmm/h'
            local lang='sv_SE.utf-8'
            day=$(LC_TIME=$lang date --date "$validTime" +'%A')

            echo -e "\n${bold}${green}${day}${default}${units}"

            temp=$date
        fi

        time=$(date --date "$validTime" '+%H:%M')
        echo -e "$time\t${bold}${blue}${t}\t${ws}\t${pmin}${default}"
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

#sort json by parameter name: pmin, t, ws
smhi_data() {
    data=$(
        curl -s $1 | jq -r '.timeSeries[].parameters|=sort_by(.name) | 
    .timeSeries[] | .validTime, (.parameters[] | 
    select(.name == ("pmin", "t", "ws")) | .values[])'
    )
}

style() {
    default='\e[0m'
    bold='\e[1m'
    green='\e[32m'
    blue='\e[94m'
}

smhi
