import time
import argparse

try:
    from rpi_ws281x import *
except:
    from neopixel_stub import *


try:
    # Python 3
    import http.client as http
except:
    # Python 2
    import httplib as http

import numpy as np
import font454
from matplotlib import colors as mcolors
COLORS = mcolors.get_named_colors_mapping()

from flask import Flask, request, render_template
app = Flask(__name__)


# LED strip configuration:
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53


class LEDLamp:
    def __init__(self, rows, columns, color=Color(255, 255, 255)):
        self.rows = rows
        self.columns = columns
        self.color = color
        self.strip = Adafruit_NeoPixel(columns=columns, rows=rows, pin=LED_PIN, freq_hz=LED_FREQ_HZ, dma=LED_DMA,
                                       invert=LED_INVERT, brightness=LED_BRIGHTNESS, channel=LED_CHANNEL)
        self.strip.begin()
        self.state = 'off' # off/all/indirect

    def setMatrixPixelColor(self, x, y, color):
        self.strip.setPixelColor(x + y * self.columns, color)

    def colorWipe(self, color, wait_ms=50):
        """Wipe color across display a pixel at a time."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def setBrightness(self, b):
        self.strip.setBrightness(b)
        self._show()

    def getBrightness(self):
        return self.strip.getBrightness()

    def _show(self):
        self.strip.show()

    def _restoreState(self):
        if self.state == 'indirect':
            self.indirect()
        if self.state == 'all':
            self.all()

    def toggleState(self):
        if self.state == 'off':
            self.all()
        elif self.state == 'all':
            self.indirect()
        elif self.state == 'indirect':
            self.off()

    def off(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()
        self.state = 'off'

    def all(self, color=None):
        if color:
            self.color = color
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, self.color)
        self.strip.show()
        self.state = 'all'

    def indirect(self, color=None):
        self.off()
        if color:
            self.color = color
        for col in range(self.columns):
            self.setMatrixPixelColor(col, 0, self.color)
            self.setMatrixPixelColor(col, self.rows-1, self.color)
        self._show()
        self.state = 'indirect'

    def rotateText(self, text, color=None, bg_color=Color(0, 0, 0), rounds=3, wait_ms=50):
        if not color:
            color = self.color
        text_length = 5 * len(text)
        buffer = np.zeros(shape=(text_length, self.rows), dtype=int)
        font454.text(buffer, text, color=color, x0=0, y0=1)

        offset = -self.columns
        round = 0
        while round < rounds:
            offset = offset+1
            if offset > max(text_length, self.columns):
                offset = -self.columns
                round += 1
            for col in range(self.columns):
                for row in range(self.rows):
                    if 0 <= (col + offset) < text_length and buffer[col + offset, row]:
                        self.setMatrixPixelColor(col, row, buffer[col + offset, row])
                    else:
                        self.setMatrixPixelColor(col, row, bg_color)

                if self.state == 'indirect' or self.state == 'all':
                    self.setMatrixPixelColor(col, 0, self.color)
                    self.setMatrixPixelColor(col, self.rows - 1, self.color)

            self._show()
            time.sleep(wait_ms / 1000.0)
        self._restoreState()

    def showText(self, text, color=None, bg_color=Color(0, 0, 0), duration_s=10):
        if color:
            self.color = color
        text_length = 5 * len(text)
        buffer = np.zeros(shape=(text_length, self.rows), dtype=int)
        font454.text(buffer, text, color=self.color, x0=0, y0=1)

        start = max(self.columns//2 - text_length, 0)
        for col in range(self.columns):
            if col < text_length:
                for row in range(self.rows):
                    if buffer[col, row]:
                        self.setMatrixPixelColor(col+start, row, buffer[col, row])
                    else:
                        self.setMatrixPixelColor(col, row, bg_color)
            if self.state == 'indirect' or self.state == 'all':
                self.setMatrixPixelColor(col, 0, self.color)
                self.setMatrixPixelColor(col, self.rows-1, self.color)
        self._show()
        if duration_s > 0:
            time.sleep(duration_s)
            self._restoreState()

    def showTime(self):
        t = time.strftime('%H:%M')
        self.rotateText(t, rounds=1)

    def showDate(self):
        d = time.strftime('%a, %d %b %Y')
        self.rotateText(d, rounds=1)

@app.route("/all")
def all():
    lamp.all()
    return ('', http.NO_CONTENT)


@app.route("/indirect")
def indirect():
    lamp.indirect()
    return ('', http.NO_CONTENT)


@app.route("/toggle")
def toggle():
    lamp.toggleState()
    return ('', http.NO_CONTENT)


@app.route("/off")
def off():
    lamp.off()
    return ('', http.NO_CONTENT)


@app.route("/state")
def state():
    return (lamp.state, http.OK)

@app.route("/date")
def showDate():
    lamp.showDate()
    return ('', http.NO_CONTENT)


@app.route("/time")
def showTime():
    lamp.showTime()
    return ('', http.NO_CONTENT)


@app.route("/text")
def text():
    t = request.args.get('t', default = "Hi Sebastian", type = str)
    lamp.rotateText(t)
    return ('', http.NO_CONTENT)


@app.route("/set")
def set():
    b = request.args.get('brightness')
    if b and 0 <= int(b) <= 255:
        lamp.setBrightness(int(b))

    c = request.args.get('color')
    if c:
        if c in COLORS:
            color = COLORS[c]
            color = color.lstrip('#')
            r,g,b = tuple(int(color[i:i+2], 16) for i in (0, 2 ,4))
            lamp.all(color=Color(r,g,b))
        else:
            return ('Color not found', http.NOT_FOUND)

    hc = request.args.get('hexcolor')
    if hc:
        r,g,b = tuple(int(hc[i:i+2], 16) for i in (0, 2 ,4))
        lamp.all(color=Color(r,g,b))

    return ('', http.NO_CONTENT)


def getHexColor():
    c = lamp.color
    w = c >> 24
    c = c - (w << 24)
    r = c >> 16
    c = c - (r << 16)
    g = c >> 8
    b = c - (g << 8)
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

@app.route("/")
def home():
    return render_template("home.html", data={'power': 'off' if lamp.state == 'off' else 'on', 'brightness': lamp.getBrightness(), 'hexcolor': getHexColor()})


if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rows', default=7, type=int)
    parser.add_argument('-c', '--columns', default=30, type=int)
    parser.add_argument('-p', '--port', default=55443, type=int)
    args = parser.parse_args()

    lamp = LEDLamp(rows=args.rows, columns=args.columns, color=Color(255, 255, 255))
    try:
        app.run(port=args.port)
    except KeyboardInterrupt:
        lamp.off()

