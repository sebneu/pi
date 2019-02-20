



import time
import argparse
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
matplotlib.use('TkAgg')

import font454

# LED strip configuration:
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53


def Color(red, green, blue, white = 0):
    """Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    return (white << 24) | (red << 16)| (green << 8) | blue


class Adafruit_NeoPixel:
    def __init__(self, columns, rows, pin, freq_hz=800000, dma=10, invert=False,
             brightness=255, channel=0):
        self.columns = columns
        self.rows = rows
        self.led_matrix = np.zeros(shape=(rows, columns))
        #self.fig = plt.figure()
        #self.ax = self.fig.subplots()
        #self.fig, self.ax = plt.subplots()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        plt.ion()
        plt.show()
        self.show()
        time.sleep(1)

    def begin(self):
        pass

    def numPixels(self):
        return self.columns * self.rows

    def setPixelColor(self, i, color):
        x = i % self.columns
        y = i // self.columns
        #print('set pixel ' + str(x)  + ' ' + str(y) + ' to color ' + str(color))
        self.led_matrix[y,x] = color

    def show(self):
        self.ax.clear()
        self.ax.imshow(self.led_matrix, cmap=plt.get_cmap("PiYG", 7))
        self.fig.canvas.draw()


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
        buffer = np.zeros(shape=(text_length, self.rows))
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
        buffer = np.zeros(shape=(text_length, self.rows))
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


if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    lamp = LEDLamp(rows=7, columns=30, color=10)

    print('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        lamp.indirect(color=3)
        #time.sleep(2)
        lamp.all()
        #time.sleep(2)
        #lamp.colorWipe(color=Color(100,50,200), wait_ms=10)
        lamp.rotateText("Hello", color=2, bg_color=0, rounds=1)
        #lamp.showDate()
        time.sleep(5)

    except KeyboardInterrupt:
        if args.clear:
            lamp.colorWipe(Color(0, 0, 0), 1)

