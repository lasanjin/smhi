#!/usr/bin/env bash

install_smhi() {
    export FILE="smhi"
    curl "https://raw.githubusercontent.com/lasanjin/smhi-cli/master/smhi.py" >~/$FILE
    chmod +x ~/$FILE
    sudo mv ~/$FILE /usr/local/bin
}

install_smhi
