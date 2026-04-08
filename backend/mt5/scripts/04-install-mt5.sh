#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING" "04-install-mt5.sh"

# Check if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    log_message "INFO" "File $mt5file already exists."
else
    log_message "INFO" "File $mt5file is not installed. Installing..."

    # Match the current MetaQuotes Linux installer guidance.
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win11" /f

    log_message "INFO" "Downloading WebView2 runtime..."
    wget -O /tmp/webview2.exe "$webview_url" > /dev/null 2>&1
    log_message "INFO" "Installing WebView2 runtime..."
    $wine_executable /tmp/webview2.exe /silent /install
    wineserver -w
    rm -f /tmp/webview2.exe

    log_message "INFO" "Downloading MT5 installer..."
    wget -O /tmp/mt5setup.exe "$mt5setup_url" > /dev/null 2>&1
    log_message "INFO" "Installing MetaTrader 5..."
    $wine_executable /tmp/mt5setup.exe /auto
    wineserver -w
    rm -f /tmp/mt5setup.exe
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    log_message "INFO" "File $mt5file is installed. Running MT5..."
    $wine_executable "$mt5file" &
else
    log_message "ERROR" "File $mt5file is not installed. MT5 cannot be run."
fi
