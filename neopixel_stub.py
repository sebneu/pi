import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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

