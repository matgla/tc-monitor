# Soldering thermocouple monitor: MAX31856 + SH1106 OLED + buzzer + button.
# Streams CSV over USB; on a Pico W also serves a live chart over Wi-Fi.
import time
import framebuf
from machine import Pin, SPI, I2C

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import config as C
from max31856 import MAX31856
from sh1106 import SH1106
from reflow import Run


class Shared:
    temp = None     # latest thermocouple temperature, None on a fault
    cj = None
    fault = 0
    ms = 0
    ip = None
    msg = None      # (hint, is_warning) from Run.message
    graph = []      # one value per 2 s for the OLED graph (about 4 min)
    hist = []       # (seq, ms, temp) every 0.5 s for the web page
    seq = 0


S = Shared()
run = Run(C)
T0 = time.ticks_ms()

spi = SPI(C.SPI_ID, baudrate=1_000_000, polarity=0, phase=1,
          sck=Pin(C.PIN_SCK), mosi=Pin(C.PIN_MOSI), miso=Pin(C.PIN_MISO))
tc = MAX31856(spi, Pin(C.PIN_CS), C.TC_TYPE, C.MAINS_HZ)
i2c = I2C(C.I2C_ID, sda=Pin(C.PIN_SDA), scl=Pin(C.PIN_SCL), freq=400_000)
oled = SH1106(i2c, C.OLED_ADDR, rotate180=C.OLED_ROTATE180)
buzzer = Pin(C.PIN_BUZZER, Pin.OUT, value=0)
button = Pin(C.PIN_BUTTON, Pin.IN, Pin.PULL_UP)

# ------------------------------------------------------------------ buzzer
PATTERNS = {
    "start": [(40, 0)],
    "soak_ok": [(300, 100), (60, 0)],        # hot air can go on
    "soak_long": [(100, 100), (100, 0)],
    "early": [(30, 60), (30, 60), (30, 0)],
    "approach": [(200, 0)],
    "tal_ok": [(60, 80), (60, 0)],           # hot air can come off
    "ramp": [(30, 60), (30, 60), (30, 0)],
    "cool_fast": [(30, 60), (30, 60), (30, 0)],
    "done": [(400, 0)],
    "fault": [(500, 300), (500, 0)],
}
_queue = []


def beep(pattern):
    _queue.extend(pattern)


async def buzzer_task():
    while True:
        if _queue:
            on, off = _queue.pop(0)
            buzzer(1)
            await asyncio.sleep_ms(on)
            buzzer(0)
            await asyncio.sleep_ms(max(off, 60))
        elif run.alarm:
            buzzer(1)
            await asyncio.sleep_ms(80)
            buzzer(0)
            await asyncio.sleep_ms(120)
        else:
            await asyncio.sleep_ms(30)


# ------------------------------------------------------------------ sampling
async def sample_task():
    await asyncio.sleep_ms(300)     # first conversion
    print("# t_ms,temp_c,cj_c,fault,state,tal_s,ramp_cps,phase,soak_s,msg")
    last_graph = last_hist = -10_000
    fault_seen = False
    while True:
        start = time.ticks_ms()
        t = time.ticks_diff(start, T0)
        f = tc.fault()
        temp = None if f & 0x43 else tc.temperature()   # open, range, OV/UV
        S.temp, S.cj, S.fault, S.ms = temp, tc.cold_junction(), f, t
        if temp is None:
            if not fault_seen and run.state == "RUN":
                beep(PATTERNS["fault"])
            fault_seen = True
        else:
            fault_seen = False
            for ev in run.update(t, temp):
                beep(PATTERNS[ev])
        msg = run.message(temp)
        S.msg = msg
        print("%d,%s,%.2f,%d,%s,%.1f,%.2f,%s,%.1f,%s" % (
            t, "" if temp is None else "%.2f" % temp, S.cj, f, run.state, run.tal,
            run.ramp, run.phase, run.soak, msg[0] if msg else ""))
        if t - last_graph >= 2000:
            last_graph = t
            S.graph.append(temp)
            if len(S.graph) > 128:
                S.graph.pop(0)
        if t - last_hist >= 500:
            last_hist = t
            S.seq += 1
            S.hist.append((S.seq, t, None if temp is None else round(temp, 2)))
            if len(S.hist) > 1200:
                S.hist.pop(0)
        spent = time.ticks_diff(time.ticks_ms(), start)
        await asyncio.sleep_ms(max(10, C.SAMPLE_MS - spent))


# ------------------------------------------------------------------ button
async def button_task():
    while True:
        if button() == 0:
            t0 = time.ticks_ms()
            long_press = False
            while button() == 0:
                if not long_press and time.ticks_diff(time.ticks_ms(), t0) > 800:
                    long_press = True
                    run.next_peak()
                    beep([(40, 100)] * (run.peak_i + 1))
                await asyncio.sleep_ms(20)
            if not long_press and time.ticks_diff(time.ticks_ms(), t0) > 30:
                if run.alarm:
                    run.mute()
                else:
                    run.clear()
                    beep([(20, 0)])
        await asyncio.sleep_ms(20)


# ------------------------------------------------------------------ display
_glyph = framebuf.FrameBuffer(bytearray(8), 8, 8, framebuf.MONO_VLSB)


def big_text(text, x, y, s=2):
    for i, ch in enumerate(text):
        _glyph.fill(0)
        _glyph.text(ch, 0, 0, 1)
        for py in range(8):
            for px in range(8):
                if _glyph.pixel(px, py):
                    oled.fill_rect(x + (i * 8 + px) * s, y + py * s, s, s, 1)


def draw_graph(top, height):
    lo, hi = 50.0, run.peak + 15
    def ypos(v):
        v = min(max(v, lo), hi)
        return top + height - 1 - int((v - lo) * (height - 1) / (hi - lo))
    for level in (C.LIQUIDUS, run.peak):
        y = ypos(level)
        for x in range(0, 128, 4):
            oled.pixel(x, y, 1)
    pts = S.graph
    x0 = 128 - len(pts)
    prev = None
    for i, v in enumerate(pts):
        if v is None:
            prev = None
            continue
        cur = (x0 + i, ypos(v))
        if prev:
            oled.line(prev[0], prev[1], cur[0], cur[1], 1)
        else:
            oled.pixel(cur[0], cur[1], 1)
        prev = cur


def draw():
    oled.fill(0)
    oled.text(run.state, 96, 0)
    oled.text("P%d" % run.peak, 96, 8)
    graph_top = 28
    if S.temp is None:
        big_text("TC ERR", 0, 0)
        oled.text(MAX31856.fault_text(S.fault) or "no data", 0, 18)
    else:
        big_text("%5.1f" % S.temp, 0, 0)
        oled.text("C", 82, 0)
        if run.state == "RUN" and S.msg:
            text, warn = S.msg
            if warn:
                oled.fill_rect(0, 17, 128, 10, 1)
                oled.text(text, 0, 18, 0)
            else:
                oled.text(text, 0, 18)
            oled.text("%+4.1f S%3d T%3d" % (run.ramp, run.soak, run.tal), 0, 29)
            graph_top = 39
        elif run.last:
            oled.text("pk%3d TAL%3ds" % (run.last["peak"], run.last["tal"]), 0, 18)
        elif S.ip:
            oled.text(S.ip, 0, 18)
    draw_graph(graph_top, 64 - graph_top)
    oled.show()


async def display_task():
    blink = False
    while True:
        draw()
        blink = run.alarm and not blink
        oled.cmd(0xA7 if blink else 0xA6)
        await asyncio.sleep_ms(250)


# ------------------------------------------------------------------ main
async def main():
    asyncio.create_task(buzzer_task())
    asyncio.create_task(sample_task())
    asyncio.create_task(button_task())
    asyncio.create_task(display_task())
    try:
        import network  # noqa: F401  (Pico W only)
        import web
        S.ip = await web.connect(C)
        await web.serve(S, run, C)
    except ImportError:
        pass
    except Exception as e:      # keep measuring without Wi-Fi
        print("# wifi:", e)
    while True:
        await asyncio.sleep(3600)


beep([(30, 0)])
asyncio.run(main())
