# Instax Photo Booth (Raspberry Pi 5 + Instax Mini Link 2)

A portable photo booth: live preview on an 8 inch touchscreen, press a button, a 3..2..1 countdown runs, the photo is taken, and it prints on a Fujifilm Instax Mini Link 2 over Bluetooth.

This is the TikTok build, rebuilt with your two changes (Instax instead of a thermal printer, Raspberry Pi 5 instead of a Pi 3). Those two swaps change more than they look, so read the next section before buying anything.

---

## What changes vs the video (read this first)

1. **No Buster.** The Pi 3 in the video runs Raspberry Pi OS "Buster." A Pi 5 cannot run Buster. You will use the current OS, **Raspberry Pi OS Bookworm (64-bit)**. The 64-bit build is required to actually use 8GB or 16GB of RAM.
2. **New camera software.** Buster used the old `raspistill` / `picamera` tools. On a Pi 5 with Bookworm those are gone. The modern library is **Picamera2**, which is what the included code uses. Any old Pi camera tutorial code will not run as-is.
3. **A special camera cable.** The Pi 5 uses a smaller camera socket (22-pin) than the camera (15-pin). You must buy a **Pi 5 camera adapter cable (22-pin to 15-pin)**. This is the single most common thing people forget.
4. **The printer is Bluetooth, not USB.** The Instax Mini Link 2 has no Linux driver. You drive it with a community library called **InstaxBLE** that talks to it over Bluetooth (the Pi 5 has Bluetooth built in). Note: InstaxBLE is confirmed working on the original Mini Link; the Mini Link 2 is listed as the same protocol but "untested," so we test safely first (the library ships with printing disabled by default, so you can run the whole pipeline without wasting film).
5. **Power is different.** The Pi 5 is power hungry (it wants 5V at 5A). Do not power it from a bare RC LiPo like the one in the video without a proper regulator and protection board. See the Power section for safe options.

---

## Shopping list

Prices are approximate, US, mid 2026. Links are official or well-known resellers; buy a local equivalent if you are outside the US.

### Required

| Part | Why you need it | Approx price | Where to buy |
| --- | --- | --- | --- |
| Raspberry Pi 5 (8GB or 16GB) | The brain. 8GB is plenty for this; 16GB is overkill but fine. | $80 / $120 | [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-5/) - [8GB CanaKit](https://www.canakit.com/raspberry-pi-5-8gb.html) - [16GB PiShop](https://www.pishop.us/product/raspberry-pi-5-16gb/) |
| Raspberry Pi Camera Module 3 | The camera. Autofocus, works with Picamera2. | $25 | [raspberrypi.com](https://www.raspberrypi.com/products/camera-module-3/) - [Adafruit](https://www.adafruit.com/product/5657) |
| Pi 5 camera cable, 22-pin to 15-pin | Connects Camera Module 3 to the Pi 5's smaller socket. Do not skip. | $6 | [Adafruit 200mm](https://www.adafruit.com/product/5818) - [Amazon](https://www.amazon.com/Official-Raspberry-Flexible-Suitable-Connect/dp/B0D12L3RDG) |
| Raspberry Pi Touch Display 2, 5 inch | The screen, with touch. Auto-detected on Bookworm with no config edits, and the box includes both ribbon cables (the Pi 5 one too) plus the GPIO power cable. | $40 | [raspberrypi.com](https://www.raspberrypi.com/products/touch-display-2/) - [The Pi Hut](https://thepihut.com/products/raspberry-pi-touch-display-2-5-portrait) |
| Fujifilm Instax Mini Link 2 | The printer. | $100 | [Amazon (Clay White)](https://www.amazon.com/Fujifilm-Instax-Mini-Smartphone-Printer/dp/B0B1NF5NBN) |
| Instax Mini film | The actual photos, about $0.75 each. Get a 20 or 40 pack. | $15 to $25 | [Amazon](https://www.amazon.com/instax-mini-link-2-film/s?k=instax+mini+link+2+film) |
| microSD card, 64GB, A2 | The Pi's storage. | $10 | [SanDisk Extreme 64GB A2](https://www.amazon.com/SanDisk-Extreme-microSDXC-Memory-Adapter/dp/B09X7C7LL1) |
| Pi 5 Active Cooler | The Pi 5 runs hot, especially in a booth enclosure. | $5 | [raspberrypi.com](https://www.raspberrypi.com/products/active-cooler/) |
| Push button | The shutter. A big arcade button feels like a real booth. | $0 to $8 | You already have one in your kit, or [Adafruit 60mm arcade button](https://www.adafruit.com/product/1185) |

### Power (pick one)

| Option | Best for | Approx price | Where to buy |
| --- | --- | --- | --- |
| Official 27W USB-C PSU | Testing and home use (plugged in). Buy this regardless, it makes setup painless. | $15 | [CanaKit](https://www.canakit.com/official-raspberry-pi-5-power-supply-27w-usb-c.html) |
| High-output USB-C PD power bank | Simplest portable option. See note below. | $40 to $80 | A quality PD bank (Anker, UGREEN, etc.), 65W or higher |
| Waveshare UPS HAT (E) | Cleanest integrated portable battery, made for the Pi 5 (5V/6A). Advanced. Needs 4x 21700 cells (sold separately). | $60 + cells | [Waveshare UPS HAT (E)](https://www.waveshare.com/ups-hat-e.htm) |

**Power note:** The Pi 5 negotiates 5V/5A only with PD supplies that explicitly offer it (most power banks top out at 5V/3A). At 5V/3A the Pi 5 still runs, but it limits USB ports and may show a low-power warning. Your booth draws very little from USB (the camera and screen do not use USB), so 5V/3A is fine in practice. Add this one line to `/boot/firmware/config.txt` to tell the Pi to allow full current and stop warning: `usb_max_current_enable=1`.

**Safety:** Do not wire a bare RC LiPo (like the red one in the video) straight to the Pi. Those need a separate 5V/5A regulator and a protection circuit, and getting it wrong is a fire risk. The UPS HAT or a PD power bank handle all of that for you.

### Optional

- Small standoffs/screws and an enclosure (3D printed, laser cut, or even a sturdy box). The teddy is optional but encouraged.

**Rough total:** about **$300** (8GB, plugged in) to roughly **$400** with 16GB or a portable battery.

---

## Build steps

### Step 1: Flash the operating system

1. On your normal computer, install **Raspberry Pi Imager** from [raspberrypi.com/software](https://www.raspberrypi.com/software/).
2. Insert the microSD card. In Imager, choose: Device = Raspberry Pi 5, OS = **Raspberry Pi OS (64-bit)**, Storage = your card.
3. Click the gear / "Edit settings." Set a username and password, your WiFi network, and tick "Enable SSH." This lets you finish setup without a keyboard if you want.
4. Write the card, put it in the Pi, and boot. Let it reach the desktop.

### Step 2: Connect and test the camera

1. With the Pi **powered off**, connect the Camera Module 3 to the Pi 5 using the 22-pin to 15-pin cable. The 22-pin (wider) end goes into the Pi's "CAM/DISP 0" port, the 15-pin end into the camera. Lift the black latch, slide the cable in with the metal contacts facing the right way (see the [official camera guide](https://www.raspberrypi.com/documentation/accessories/camera.html)), then press the latch down.
2. Boot the Pi, open a Terminal, and run:
   ```bash
   rpicam-hello -t 5000
   ```
   You should see a 5 second live preview. If you do, the camera works. (On Bookworm the camera is auto-detected, no "enable camera" step needed.)

### Step 3: Connect and test the screen

The Touch Display 2 needs only two connections and no config file edits. The touch drivers are already in Raspberry Pi OS.

1. Power off. Connect the included **22-way to 15-way ribbon cable** between the display and the Pi's free **DSI/CAM port** (the one the camera is not using). The smaller (22-way) end goes to the Pi, contacts seated correctly, latch closed.
2. Connect the included **GPIO power cable**: red wire to **pin 2 (5V)** and black wire to **pin 6 (GND)** on the Pi's 40-pin header. The display is powered entirely by the Pi, so it needs no separate supply.
3. Boot. The desktop should appear on the screen and respond to touch immediately. Step-by-step with photos: [official install guide](https://www.raspberrypi.com/documentation/accessories/touch-display-2.html).
4. The panel is portrait (720 x 1280). For a landscape booth, open **Screen Configuration** (or `raspi-config`) and rotate to landscape, then set `PREVIEW_SIZE` in `booth.py` to match: `(1280, 720)` for landscape or `(720, 1280)` for portrait.

### Step 4: Wire the button

Wire a momentary push button between **GPIO17 (physical pin 11)** and a **GND pin (use pin 9, since pin 6 is taken by the display power)**. No resistor needed, the code enables the Pi's internal pull-up. Pinout reference: [pinout.xyz](https://pinout.xyz/).

### Step 5: Sort out power

For setup, use the official 27W USB-C supply. For portable use, plug in your PD power bank (and add `usb_max_current_enable=1` to `/boot/firmware/config.txt`), or fit the UPS HAT (E) per its wiki. See the Power note above.

### Step 6: Install the software

Open a Terminal on the Pi and run:

```bash
# Make a project folder
mkdir ~/instax-photobooth && cd ~/instax-photobooth

# Create a virtual environment that can still see the system camera library.
# The --system-site-packages flag is important: Picamera2 and gpiozero are
# installed system-wide and cannot be pip-installed into a plain venv.
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install the extra Python packages we need
pip install simplepyble pillow pygame numpy

# Get the Instax Bluetooth library (creates an "InstaxBLE" folder here)
git clone https://github.com/javl/InstaxBLE.git
```

Now put `booth.py` (the included file) into `~/instax-photobooth/`. Your folder should look like:

```
instax-photobooth/
  venv/
  InstaxBLE/      (the cloned repo, contains InstaxBLE.py)
  booth.py
```

If `pip install simplepyble` fails to build, install the Bluetooth dev headers and retry:
```bash
sudo apt install -y libdbus-1-dev
pip install simplepyble
```

### Step 7: Find the printer and do a safe dry run

1. Turn the Instax Mini Link 2 on and load film.
2. Find its Bluetooth name. With your venv active:
   ```bash
   python3 - <<'PY'
   import simplepyble
   a = simplepyble.Adapter.get_adapters()[0]
   a.scan_for(5000)
   for p in a.scan_get_results():
       if "INSTAX" in (p.identifier() or ""):
           print("name:", p.identifier(), " address:", p.address())
   PY
   ```
   Note the name (something like `INSTAX-12345678(IOS)`).
3. The code auto-finds the printer by default. If the scan above showed a name that does **not** end in `(IOS)`, open `booth.py` and set `DEVICE_NAME = "INSTAX-12345678"` (drop the `(IOS)`/`(ANDROID)` part) or set `DEVICE_ADDRESS` to the address shown.
4. Leave `PRINT_ENABLED = False` (the default) and run it:
   ```bash
   python3 booth.py
   ```
   Press the button. You should see the countdown, the capture, and "Saved (TEST MODE, no print)." This proves camera, screen, button, and the Bluetooth link to the printer all work, without using any film. Press ESC to quit.

### Step 8: First real print

Once the dry run works, open `booth.py`, set:

```python
PRINT_ENABLED = True
```

Save, run `python3 booth.py` again, and press the button. The Mini Link 2 should print. Each shot ejects in about 12 to 15 seconds and finishes developing in roughly 90 seconds.

### Step 9 (optional): Start the booth automatically on boot

So it runs without a keyboard:

1. Enable auto-login to the desktop: `sudo raspi-config` -> System Options -> Boot / Auto Login -> Desktop Autologin.
2. Create a launcher script `~/instax-photobooth/run.sh`:
   ```bash
   #!/bin/bash
   cd ~/instax-photobooth
   source venv/bin/activate
   python3 booth.py
   ```
   Make it executable: `chmod +x ~/instax-photobooth/run.sh`.
3. Add it to the desktop autostart. The exact file depends on your desktop version, so the most reliable route is a user service: see the Raspberry Pi docs for "run a program at startup." Test by rebooting.

---

## Verification checklist

Tick these off in order. Each one isolates a different part, so if something breaks you know exactly where.

- [ ] `rpicam-hello -t 5000` shows a live image (camera + cable good)
- [ ] Desktop appears on the 8 inch screen and touch works (display good)
- [ ] The scan snippet in Step 7 prints your `INSTAX-...` name (Bluetooth good)
- [ ] Dry run (`PRINT_ENABLED = False`) reaches "Saved (TEST MODE, no print)" (full pipeline good)
- [ ] Real run (`PRINT_ENABLED = True`) produces a printed photo (done)

---

## Troubleshooting

- **Camera not detected / black preview:** Re-seat the ribbon cable at both ends, contacts facing the right way, latches closed. Make sure you used the 22-to-15-pin Pi 5 cable, not the cable that came with the camera.
- **Screen stays black:** Check the ribbon cable is fully seated at both ends with the contacts the right way, and that the GPIO power cable is on pin 2 (5V) and pin 6 (GND). The Touch Display 2 is auto-detected, so there is no overlay or config line to add.
- **Preview colours look swapped (blue faces):** In `booth.py`, the `preview_surface()` function flips BGR to RGB with `rgb = frame[:, :, ::-1]`. If your build shows swapped colours, remove that flip (use `rgb = frame`). The saved/printed photo uses a separate correct path and is not affected.
- **Printer never found:** Make sure it is on and not connected to your phone's Instax app at the same time (it pairs with one device). Set `DEVICE_NAME` or `DEVICE_ADDRESS` from the scan. If a print ever leaves an orange light on the printer, turn it off and on to reset.
- **"Low power" warning or random reboots:** Use the official 27W supply, or add `usb_max_current_enable=1` to `/boot/firmware/config.txt` when on a power bank.
- **`picamera2` not found inside the venv:** You created the venv without `--system-site-packages`. Recreate it with that flag (Step 6).

---

## How this differs from the thermal-printer version

The video's thermal printer is instant, costs pennies per print, and produces a monochrome receipt-style strip. Your Instax version produces real color instant-film keepsakes, but each shot costs about $0.75, takes about a minute to fully develop, and the integration is community-reverse-engineered rather than a plug-in driver. That is the trade you are choosing, and for a photo booth the nicer prints are usually worth it.

---

## Sources

- InstaxBLE library and supported-model list: https://github.com/javl/InstaxBLE
- InstaxBLE Raspberry Pi fork: https://github.com/fernandi/InstaxBLE-Pi
- Pi 5 camera cable (22-pin to 15-pin): https://www.adafruit.com/product/5818
- Raspberry Pi camera documentation: https://www.raspberrypi.com/documentation/accessories/camera.html
- Camera Module 3: https://www.raspberrypi.com/products/camera-module-3/
- Raspberry Pi Touch Display 2 (5 inch, $40) and install guide: https://www.raspberrypi.com/products/touch-display-2/ and https://www.raspberrypi.com/documentation/accessories/touch-display-2.html
- Picamera2 in a virtual environment (use --system-site-packages): https://forums.raspberrypi.com/viewtopic.php?t=361758
- Pi 5 power requirements: https://www.canakit.com/official-raspberry-pi-5-power-supply-27w-usb-c.html
- Waveshare UPS HAT (E) for Pi 5: https://www.waveshare.com/ups-hat-e.htm
- Instax Mini Link 2: https://www.amazon.com/Fujifilm-Instax-Mini-Smartphone-Printer/dp/B0B1NF5NBN
