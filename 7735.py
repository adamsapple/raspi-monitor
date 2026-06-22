import board
import digitalio
from adafruit_rgb_display import st7735
from gpiozero import Button
from PIL import Image, ImageDraw, ImageOps, ImageFont

import signal
import socket
import time
from decimal import Decimal, ROUND_HALF_UP
import math

from app.stats import Stats
from app.aligner import Aligner
from app.frameoperator import FrameOperator
from app.displayblinker import DisplayBlinker
from app.fancontroller import FanController



# Configuration for CS and DC pins (these are PiTFT defaults):
btn_pinid = board.D23.id
cs_pin    = digitalio.DigitalInOut(board.D24)
dc_pin    = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D22)
bl_pin    = digitalio.DigitalInOut(board.D0)    #backlight pin (if used)


# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

FONT1_SIZE        = 14
FONT2_SIZE        = 12
FONT1_PATH        = f"./fonts/ter-u{FONT1_SIZE}n.pil"   # makePilFont.py で作成した PIL font を指定
#FONT2_PATH        = f"./fonts/ter-u{FONT2_SIZE}n.pil"   # makePilFont.py で作成した PIL font を指定
#FONT2_PATH        = f"fonts/HaxorMedium-10.pil"
#FONT2_PATH        = f"fonts/6x10.pil"
FONT2_PATH        = "./fonts/ter-u12n.pil"
FONT3_PATH        = "./fonts/Bm5x8.pil"


UPDATE_INTERVAL   = 0.5           # info update interval.
BLACK_INTERVAL    = 60
NETWORK_INTERFACE = "wlan0"   # put ip from this network interface.
STORAGE_PARTITION = f"/dev/nvme0n1p2"

# ----- state -----
STATE_BOOTSTRAP = 0
STATE_RUNNING   = 1

state = STATE_BOOTSTRAP
state_change_at = 0

# ----- pages -----
PAGE_OVERVIEW = 0
PAGE_CPU      = 1
PAGE_NET      = 2
PAGE_COUNT    = 3
page = PAGE_OVERVIEW

def next_page():
    global page
    page = (page + 1) % PAGE_COUNT

# ----- colors -----
BG_COLOR     = "#1f1f28"
FG_COLOR     = "#dcc98d"
ACCENT_COLOR = "#7e9cd8"
WARN_COLOR   = "#ff9552"
ERROR_COLOR  = "#f13c31"
GREEN_COLOR  = "#96b96b"
MUTED_COLOR  = "#54546d"

# Setup SPI bus using hardware SPI:
spi  = board.SPI()
disp = st7735.ST7735R(spi,# rotation=270
    # x_offset=2, y_offset=1, bgr=True,  # 128x160
    x_offset=2, y_offset=1, height=128, bgr=False,  # 128x128
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)


# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
if disp.rotation in (90, 270):
    width  = disp.height
    height = disp.width
else:
    width  = disp.width
    height = disp.height

print(f"{width} x {height}")
#print(f"IP: {ipget.ipget().ipaddr(NETWORK_INTERFACE)}")
disp.init()
disp.fill(0)

image  = Image.new("RGB", (width, height))
fan_img = Image.open('./icons/icon_fan_24.png')
font1  = ImageFont.load(FONT1_PATH)
font2  = ImageFont.load(FONT2_PATH)
font3  = ImageFont.load(FONT3_PATH)
draw   = ImageDraw.Draw(image)

stats   = Stats(UPDATE_INTERVAL, NETWORK_INTERFACE, STORAGE_PARTITION)
frame   = FrameOperator()
aligner = Aligner()
blinker = DisplayBlinker(btn_pinid, bl_pin, BLACK_INTERVAL)
casefan = FanController()

blinker.on_pushed = next_page

##
# bootstrap animation.
#
def draw_startup_animation(is_visible: bool = True):
    base_color  = "#16161d"     # "#4dd0ff"
    frame_color = "#cdc8ae"      # "#4dd0ff"
    bg_color    = "#1f1f28"   # "#10253b"

    primary_color   = "#dcc98d"   # "#ffffff"
    secondary_color = "#957fb8"     # "#7cf7ff"
    third_color     = "#54546d"     #"#9be3ff"    
    inverted_color  = "#202a3c"     # "#1f1f28"
    warn_color  = "#ff9552"
    error_color = "#f13c31"
    info_color  = "#4686ab"
    green_color = "#96b96b"

    draw.rectangle((0, 0, width, height), outline=0, fill=base_color)
    if not is_visible:
        return

    host = socket.gethostname().upper()
    frame_x = 4
    frame_y = 4
    frame_w = width - 8
    frame_h = height - 8

    # outer frame、background を描画
    draw.rectangle((frame_x, frame_y, frame_x + frame_w - 1, frame_y + frame_h - 1),
                   outline=frame_color, fill=bg_color   , width=1)

    draw.rectangle((frame_x + 2, frame_y + 2 , frame_x + frame_w - 1 - 2, frame_y + frame_h - 1 - 2),
                   outline=frame_color, width=1, fill=None)
    
    # welcome
    draw.text((frame_x + 6, frame_y + 8), "WELCOME", font=font2, fill=secondary_color)
    draw.text((frame_x + 6, frame_y + 22), host, font=font1, fill=primary_color)

    # animation
    scan = int((time.time() * 8) % 6)
    for i in range(6):
        x = frame_x + 8 + i * 10
        y = frame_y + 42 + ((i + scan) % 2) * 4
        color = secondary_color if i == scan else third_color
        draw.rectangle((x, y, x + 7, y + 4), outline=color, fill=inverted_color, width=1)

    # ip address
    x = frame_x + 8
    y = frame_y + 42 + 20
    draw.text((x, y), f"IP:{stats.ip}", font=font2, fill=green_color)

    # progress bar
    pulse = int((time.time() * 10) % (width - 24))
    draw.rectangle((frame_x + 8, frame_h - 18, frame_x + 8 + pulse, frame_h - 12),
                   outline=secondary_color, fill=third_color, width=1)
    draw.text((frame_x + 8, frame_h - 32), "bootstrap...".upper(), font=font2, fill=third_color)

##
# update bootstrap state.
#
def update_bootstrap() -> None:
    global state
    global state_change_at
    
    if state != STATE_BOOTSTRAP:
        return
    
    if state_change_at == 0:
        if stats.ip != "unknown":
            print(f"IP acquired: {stats.ip}")
            state_change_at = time.time() + 5.0
    else:
        #print(f"time: {state_change_at - time.time():.1f} sec remaining until state change.")
        if time.time() >= state_change_at:
            state = STATE_RUNNING

##
#
#
def draw_stats(is_visible:bool = True):
    #disp.fill(0x7521)
    #disp.pixel(64, 64, 0)
    draw.rectangle((0, 0, width, height), outline=0, fill="#1f1f28")

    if not is_visible:
        return

    y = 0
    row1 = FONT1_SIZE+1
    row2 = FONT2_SIZE+1

    (fleft, ftop, fright, fbottom) = font2.getbbox('A')
    font_height = fbottom - ftop + 1
    font2_width = fright - fleft
    word_count  = math.floor(width / font2_width)
    x = font2_width / 2

    draw.text((0, y), f"Time: {time.strftime('%H:%M:%S')}", font=font1, fill="#dcc98d")
    y += row1

    # ip
    draw.text((0, y), aligner.formattedMsg(f"IP:*{stats.ip}", word_count), font=font2, fill="#dcc98d")
    y += row2

    # cpu
    draw.text((x, y), aligner.formattedMsg("CPU:{:>3.0f}%".format(stats.cpu) +  " *{:.1f}°c".format(stats.temp), word_count-1), font=font2, fill="#dcc98d")
    y += row2
    
    # memory
    draw.text((x, y), aligner.formattedMsg(f"Mem: {stats.usedMemPercent:>.0f}%", word_count-1), font=font2, fill="#dcc98d")
    y += row2
    draw.text((x, y), aligner.formattedMsg(f"    {(stats.usedMem):.1f} / {(stats.totalMem):.1f}GB", word_count-1), font=font3, fill="#dcc98d")
    y += row2
    
    # disk
    disk_percent = stats.diskUseGB * 100 / stats.diskTotalGB
    draw.text((x, y), aligner.formattedMsg(f"Dsk: {disk_percent:>.0f}%", word_count-1), font=font2, fill="#dcc98d")
    y += row2
    draw.text((x, y), f"   {stats.diskUseGB:.1f} / {stats.diskTotalGB:.1f}GB", font=font3, fill="#dcc98d")
    y += row2
    y += row2 * 0.5

    # fan
    num = Decimal(stats.cpu_fan_percentage)
    draw.text((x, y), aligner.formattedMsg(f"Fan RPM: {stats.cpu_fan_rpm}({num.quantize(Decimal('1'), rounding=ROUND_HALF_UP)}%)", word_count-1), font=font2, fill="#dcc98d")
    #image.paste(fan_img, (x+30, y))
    y += row2
    
    # casefan
    num = Decimal(stats.cpu_fan_percentage)
    draw.text((x, y), aligner.formattedMsg(f"Case: {casefan.temp:.0f}°c ({casefan.fan_speed}%", word_count-1), font=font2, fill="#dcc98d")
    y += row2
    
    #inverted_img = ImageOps.invert(image)
    #disp.image(inverted_img)

def draw_page_cpu():
    draw.rectangle((0, 0, width, height), fill=BG_COLOR)
    draw.text((2, 0), "CPU / TEMP", font=font2, fill=FG_COLOR)
    draw.text((2, 20), f"CPU {stats.cpu:>3.0f}%", font=font2, fill=FG_COLOR)

def draw_page_net():
    draw.rectangle((0, 0, width, height), fill=BG_COLOR)
    draw.text((2, 0), "NETWORK", font=font2, fill=FG_COLOR)

##
#
#
def human_bps(bps):
    units = ["B/s", "K/s", "M/s", "G/s"]
    v, i = float(bps), 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.1f}{units[i]}"

##
#
#
def draw_sparkline(rect, series, vmin, vmax, color):
    x0, y0, x1, y1 = rect
    draw.rectangle(rect, outline=MUTED_COLOR, fill=None)
    w, h = (x1 - x0), (y1 - y0)
    vals = series.values()[-(w + 1):]      # 1px=1サンプル、最新を右端に
    if len(vals) < 2:
        return
    span = (vmax - vmin) or 1.0
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = x1 - (n - 1 - i)
        norm = max(0.0, min(1.0, (v - vmin) / span))
        pts.append((x, y1 - norm * h))
    draw.line(pts, fill=color, width=1)


##
# update stats and other info.
#
def main():
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    
    try:
        frame.func = update_frame
        frame.start()

    except KeyboardInterrupt:
        print("Keyboard Interrupt detected.\nExit.")
    #except Exception as e:
    #   print("Unknown exception detected.\nExit.")
    #   print(e)
    finally:
        terminate()

##
# frame update function.
#     
def update_frame():
    # pages = dict(int, function)

    blinker.update()
    stats.update()
    casefan.update()
    
    if state == STATE_BOOTSTRAP:
        update_bootstrap()
        draw_startup_animation(True)
    elif state == STATE_RUNNING:
        if not blinker.is_visible:
            draw.rectangle((0, 0, width, height), fill=0)
        elif page == PAGE_OVERVIEW:
            draw_stats(True)            # 既存の関数をそのまま使用
        elif page == PAGE_CPU:
            draw_page_cpu()
        elif page == PAGE_NET:
            draw_page_net()

    disp.image(image)
    

##
# signal handler.
#
def handler(signum, frame):
    print("signal={}".format(signum))
    frame.stop()

##
# termination process.
#
def terminate():
    casefan.close()
    disp.fill(0)
    blinker.is_visible = False
    exit(0)

##
# main entry.
#
if __name__ == "__main__":
    main()
