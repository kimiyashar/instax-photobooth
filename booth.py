#!/usr/bin/env python3
"""
Instax Photo Booth for Raspberry Pi 4 - vintage lace UI, landscape.
welcome -> tap anywhere -> live mirror -> tap the "ready?" hand -> 3-2-1 ->
photo -> print -> "that's all folks".
Live preview is mirrored (like a real mirror). Only the "ready?" hand corner
starts the countdown, so tapping the preview won't trigger it.
"""

import os
import sys
import time
from datetime import datetime

import numpy as np
import pygame
from PIL import Image
from picamera2 import Picamera2

from InstaxBLE.InstaxBLE import InstaxBLE
try:
    from InstaxBLE import LedPatterns
except Exception:
    LedPatterns = None

# ---------------------------------------------------------------------------
PRINT_ENABLED = True
DEVICE_NAME   = "INSTAX-15358106"
DEVICE_ADDRESS = None

SCREEN_ROTATE = 90
PRINT_ROTATE  = 0
PRINT_WAIT    = 25

MIRROR_PREVIEW = True     # flip the LIVE view like a real mirror.
FLIP_PREVIEW_V = False    # set True if the live view is upside-down
MIRROR_PRINT   = False    # set True to also mirror the PRINTED photo

# The "ready?" hand tap target, in CANVAS coords (1280x720 landscape).
# Only taps inside this box start the countdown. Nudge these numbers to
# move/resize the target if needed. (x1, y1, x2, y2)
READY_ZONE = (1015, 120, 1280, 380)

HERE      = os.path.dirname(os.path.abspath(__file__))
ASSETS    = os.path.join(HERE, "assets")
PHOTO_DIR = os.path.expanduser("~/booth-photos")

CANVAS_W, CANVAS_H = 1280, 720
OPENING = (254, 45, 771, 629)
COUNTDOWN_SECONDS = 3
COUNTDOWN_H = 200
OUTRO_SECONDS = 3
CONNECT_TIMEOUT = 15
INSTAX_RATIO = 600 / 800

# ---------------------------------------------------------------------------
os.makedirs(PHOTO_DIR, exist_ok=True)

picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(
    main={"size": (1280, 720), "format": "RGB888"},
    raw={"size": (2304, 1296)},
)
still_config = picam2.create_still_configuration()
picam2.configure(preview_config)
picam2.start()
time.sleep(1)

pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_W, SCREEN_H = screen.get_size()


def load_img(name, alpha=False):
    img = pygame.image.load(os.path.join(ASSETS, name))
    return img.convert_alpha() if alpha else img.convert()

IMG_IDLE   = load_img("idle.png")
IMG_FRAME  = load_img("frame_bg.png")
IMG_FLORAL = load_img("frame_florals.png", alpha=True)
IMG_OUTRO  = load_img("outro.png")
IMG_CD = {3: load_img("cd3.png", alpha=True),
          2: load_img("cd2.png", alpha=True),
          1: load_img("cd1.png", alpha=True)}
IMG_HAND = load_img("hand.png", alpha=True)   # "ready?" hand, shown ONLY on preview

PREVIEW_W = int(OPENING[3] * INSTAX_RATIO)
PREVIEW_H = OPENING[3]
PREVIEW_X = OPENING[0] + (OPENING[2] - PREVIEW_W) // 2
PREVIEW_Y = OPENING[1]

instax = None


def blit_canvas(canvas):
    rotated = pygame.transform.rotate(canvas, SCREEN_ROTATE)
    rect = rotated.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
    screen.fill((0, 0, 0)); screen.blit(rotated, rect); pygame.display.flip()


def camera_preview_surface():
    frame = picam2.capture_array()
    h, w, _ = frame.shape
    target = INSTAX_RATIO
    if w / h > target:
        cw = int(h * target); x0 = (w - cw) // 2; crop = frame[:, x0:x0 + cw]
    else:
        ch = int(w / target); y0 = (h - ch) // 2; crop = frame[y0:y0 + ch, :]
    crop = crop[:, :, ::-1]                 # BGR -> RGB
    # NOTE: screen is rotated 90 deg, so axes are swapped vs. what you see.
    # Reversing rows (axis 0) = left-right mirror ON SCREEN.
    if MIRROR_PREVIEW:
        crop = crop[::-1, :, :]             # mirror left-right (on the rotated display)
    if FLIP_PREVIEW_V:
        crop = crop[:, ::-1, :]             # flip upside-down (on the rotated display)
    surf = pygame.surfarray.make_surface(np.ascontiguousarray(crop.swapaxes(0, 1)))
    return pygame.transform.smoothscale(surf, (PREVIEW_W, PREVIEW_H))


def draw_live(extra=None, show_hand=False):
    canvas = pygame.Surface((CANVAS_W, CANVAS_H))
    canvas.blit(IMG_FRAME, (0, 0))
    canvas.blit(camera_preview_surface(), (PREVIEW_X, PREVIEW_Y))
    canvas.blit(IMG_FLORAL, (0, 0))
    if show_hand:
        canvas.blit(IMG_HAND, (0, 0))
    if extra is not None:
        ew, eh = extra.get_size(); s = COUNTDOWN_H / eh
        small = pygame.transform.smoothscale(extra, (int(ew * s), int(eh * s)))
        canvas.blit(small, small.get_rect(center=(CANVAS_W // 2, CANVAS_H // 2)))
    blit_canvas(canvas)


def show_static(image, seconds=0.0):
    canvas = pygame.Surface((CANVAS_W, CANVAS_H)); canvas.blit(image, (0, 0))
    blit_canvas(canvas)
    if seconds:
        time.sleep(seconds)


def photo_in_frame(final_path):
    photo = pygame.image.load(final_path).convert()
    canvas = pygame.Surface((CANVAS_W, CANVAS_H))
    canvas.blit(IMG_FRAME, (0, 0))
    ps = pygame.transform.smoothscale(photo, (PREVIEW_W, PREVIEW_H))
    canvas.blit(ps, (PREVIEW_X, PREVIEW_Y))
    canvas.blit(IMG_FLORAL, (0, 0))
    blit_canvas(canvas)


def connect_printer():
    global instax
    try:
        if instax is not None:
            try:
                instax.disconnect()
            except Exception:
                pass
        instax = InstaxBLE(device_name=DEVICE_NAME, device_address=DEVICE_ADDRESS,
                           print_enabled=PRINT_ENABLED, quiet=True)
        instax.connect(timeout=CONNECT_TIMEOUT)
        if not (instax.peripheral and instax.peripheral.is_connected()):
            instax = None
    except Exception as e:
        print("Printer connect error:", e)
        instax = None
    return instax is not None


def crop_to_portrait(path_in, path_out):
    img = Image.open(path_in)
    if PRINT_ROTATE:
        img = img.rotate(-PRINT_ROTATE, expand=True)
    w, h = img.size
    if w / h > INSTAX_RATIO:
        nw = int(h * INSTAX_RATIO); left = (w - nw) // 2
        img = img.crop((left, 0, left + nw, h))
    else:
        nh = int(w / INSTAX_RATIO); top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    if MIRROR_PRINT:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img.save(path_out, "JPEG", quality=95)


def capture_and_print():
    global instax
    for n in range(COUNTDOWN_SECONDS, 0, -1):
        draw_live(extra=IMG_CD.get(n))
        time.sleep(1)

    flash = pygame.Surface((CANVAS_W, CANVAS_H)); flash.fill((255, 255, 255))
    show_static(flash, 0.12)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    raw_path = os.path.join(PHOTO_DIR, f"{stamp}-raw.jpg")
    final_path = os.path.join(PHOTO_DIR, f"{stamp}.jpg")
    picam2.switch_mode_and_capture_file(still_config, raw_path)
    crop_to_portrait(raw_path, final_path)
    photo_in_frame(final_path)

    if PRINT_ENABLED:
        try:
            picam2.stop()
        except Exception:
            pass
        time.sleep(0.5)
        connect_printer()
        if instax is not None:
            try:
                if LedPatterns is not None:
                    instax.send_led_pattern(LedPatterns.rainbow, when=1)
                    instax.send_led_pattern(LedPatterns.pulseGreen, when=2)
                instax.print_image(final_path)
                time.sleep(PRINT_WAIT)
            except Exception as e:
                print("Print error:", e)
            try:
                instax.disconnect()
            except Exception:
                pass
            instax = None
        try:
            picam2.start()
            time.sleep(1)
        except Exception:
            pass
    else:
        time.sleep(5)

    show_static(IMG_OUTRO, OUTRO_SECONDS)


def to_canvas(sx, sy):
    """Map a physical touch/mouse point to CANVAS coords, undoing the 90 deg rotation."""
    rw, rh = CANVAS_H, CANVAS_W          # rotated canvas is 720 wide x 1280 tall
    rect_left = (SCREEN_W - rw) / 2.0
    rect_top  = (SCREEN_H - rh) / 2.0
    rx = sx - rect_left
    ry = sy - rect_top
    cx = (CANVAS_W - 1) - ry
    cy = rx
    return cx, cy


def in_ready_zone(sx, sy):
    cx, cy = to_canvas(sx, sy)
    x1, y1, x2, y2 = READY_ZONE
    return x1 <= cx <= x2 and y1 <= cy <= y2


def get_tap():
    """Returns ('quit', None) | ('tap', (sx, sy)) | (None, None)."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit", None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit", None
        if event.type == pygame.FINGERDOWN:
            return "tap", (event.x * SCREEN_W, event.y * SCREEN_H)
        if event.type == pygame.MOUSEBUTTONDOWN:
            return "tap", event.pos
    return None, None


def wait_for_tap():
    """Idle screen: any tap advances to the live preview."""
    last = 0
    while True:
        ev, _ = get_tap()
        if ev in ("tap", "quit"):
            return ev
        if time.time() - last > 1.0:
            show_static(IMG_IDLE); last = time.time()
        pygame.time.wait(10)


def live_until_ready():
    """Live preview: only a tap on the 'ready?' hand starts the countdown."""
    pygame.event.clear()
    while True:
        ev, pos = get_tap()
        if ev == "quit":
            return "quit"
        if ev == "tap" and pos is not None and in_ready_zone(*pos):
            return "tap"
        draw_live(show_hand=True)


def main():
    while True:
        show_static(IMG_IDLE, 0)
        if wait_for_tap() == "quit":
            break
        if live_until_ready() == "quit":
            break
        capture_and_print()
    picam2.stop()
    if instax is not None:
        try:
            instax.disconnect()
        except Exception:
            pass
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        picam2.stop()
        try:
            if instax is not None:
                instax.disconnect()
        except Exception:
            pass
        pygame.quit()
        sys.exit()
