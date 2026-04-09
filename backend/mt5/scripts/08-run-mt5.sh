#!/bin/bash

source /scripts/02-common.sh

log_message "RUNNING" "08-run-mt5.sh"

if ! resolved_mt5file=$(resolve_mt5_file); then
    log_message "ERROR" "MetaTrader 5 executable was not found in the Wine prefix."
    exit 1
fi

log_message "INFO" "Launching MetaTrader 5 from $resolved_mt5file"
$wine_executable "$resolved_mt5file" &
