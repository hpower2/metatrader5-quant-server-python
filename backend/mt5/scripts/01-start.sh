#!/bin/bash

# Source common variables and functions
source /scripts/02-common.sh

if [ -n "$DISPLAY" ] && [ -z "$MT5_STARTUP_XTERM" ] && command -v /usr/bin/xterm >/dev/null 2>&1; then
    export MT5_STARTUP_XTERM=1
    exec /usr/bin/xterm -fa Monospace -fs 11 -geometry 140x36+20+20 -title "MT5 Startup" \
        -e /bin/bash -lc 'export MT5_STARTUP_XTERM=1; /scripts/01-start.sh'
fi

# Run installation scripts
/scripts/03-install-mono.sh
/scripts/04-install-mt5.sh
/scripts/05-install-python.sh
/scripts/06-install-libraries.sh

# Start servers
/scripts/07-start-wine-flask.sh

# Keep a visible log stream in the VNC startup terminal.
touch /config/mt5_setup.log
tail -n 50 -f /config/mt5_setup.log
