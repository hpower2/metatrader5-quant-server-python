#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING" "04-install-mt5.sh"

# Check if MetaTrader 5 is installed
if resolved_mt5file=$(resolve_mt5_file); then
    log_message "INFO" "MetaTrader 5 is already installed at $resolved_mt5file."
else
    log_message "INFO" "File $mt5file is not installed. Installing..."

    # Match the current MetaQuotes Linux installer guidance.
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win11" /f

    if has_webview2_runtime; then
        log_message "INFO" "WebView2 runtime already exists in the Wine prefix. Skipping install."
    else
        log_message "INFO" "Downloading WebView2 runtime..."
        wget -O /tmp/webview2.exe "$webview_url" > /dev/null 2>&1
        log_message "INFO" "Installing WebView2 runtime..."
        timeout 300 $wine_executable /tmp/webview2.exe /silent /install
        wait_for_wineserver 180
        rm -f /tmp/webview2.exe
    fi

    log_message "INFO" "Downloading MT5 installer..."
    wget -O /tmp/mt5setup.exe "$mt5setup_url" > /dev/null 2>&1
    log_message "INFO" "Installing MetaTrader 5..."
    timeout 600 $wine_executable /tmp/mt5setup.exe /auto
    wait_for_wineserver 300
    rm -f /tmp/mt5setup.exe
fi

# Recheck if MetaTrader 5 is installed
if resolved_mt5file=$(resolve_mt5_file); then
    log_message "INFO" "MetaTrader 5 is installed at $resolved_mt5file. Running MT5..."
    /scripts/08-run-mt5.sh
else
    log_message "ERROR" "MetaTrader 5 is not installed. MT5 cannot be run."
fi
