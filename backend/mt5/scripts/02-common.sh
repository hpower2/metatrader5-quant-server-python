#!/bin/bash

# Set variables
mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
webview_url="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe"
mt5file="/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
python_url="https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe"
wine_executable="wine"
metatrader_version="5.0.36"
mt5server_port=18812
mt5_log_file="/config/mt5_setup.log"

# Function to show messages
log_message() {
    local level=$1
    local message=$2
    local formatted_message
    formatted_message="$(date '+%Y-%m-%d %H:%M:%S') - [$level] $message"
    echo "$formatted_message" | tee -a "$mt5_log_file" >/dev/null
}

resolve_mt5_file() {
    local detected_mt5file

    if [ -f "$mt5file" ]; then
        echo "$mt5file"
        return 0
    fi

    detected_mt5file=$(find /config/.wine/drive_c -type f \( -iname 'terminal64.exe' -o -iname 'terminal.exe' \) \
        -path '*/MetaTrader 5/*' 2>/dev/null | head -n 1)

    if [ -n "$detected_mt5file" ]; then
        mt5file="$detected_mt5file"
        echo "$mt5file"
        return 0
    fi

    return 1
}

has_webview2_runtime() {
    find /config/.wine/drive_c -type f -path '*/Microsoft/EdgeWebView/Application/*/msedgewebview2.exe' \
        2>/dev/null | grep -q .
}

wait_for_wineserver() {
    local timeout_seconds="${1:-120}"

    if timeout "$timeout_seconds" wineserver -w; then
        return 0
    fi

    log_message "WARN" "wineserver -w timed out after ${timeout_seconds}s; continuing startup."
    return 1
}

# Function to check if a Python package is installed in Wine
is_wine_python_package_installed() {
    $wine_executable python -c "import pkg_resources; pkg_resources.require('$1')" 2>/dev/null
    return $?
}

# Function to check if a Python package is installed in Linux
is_python_package_installed() {
    python3 -c "import pkg_resources; pkg_resources.require('$1')" 2>/dev/null
    return $?
}

# Mute Unnecessary Wine Errors
export WINEDEBUG=-all,err-toolbar,fixme-all
