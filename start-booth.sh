#!/bin/bash
# Instax Photo Booth autostart.
# Runs only on the main screen (tty1). On any other console it just exits,
# so you can still get a normal terminal (Ctrl+Alt+F2).

[ "$(tty)" = "/dev/tty1" ] || exit 0

echo ""
echo "  Photo booth starting in 3 seconds..."
echo "  Press Ctrl+C now if you want a terminal instead."
sleep 3

# make sure Bluetooth is on for the printer
sudo rfkill unblock bluetooth 2>/dev/null
bluetoothctl power on 2>/dev/null

cd "$HOME/instax-photobooth" || exit 0
source venv/bin/activate
exec python booth.py
