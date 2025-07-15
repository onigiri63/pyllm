from time import time
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import threading
import psutil
import math


class DynamicPlot(tk.Tk):
    graph_update_rate = .1  # seconds per update
    newDataReady = False
    minimize_event = threading.Event
    def __init__(self, title, miny, minx, offsetX, offsetY, root, breakout: list):
        super().__init__()
        self.breakout = breakout
        minY = 0
        maxY = 0
        self.offsetX = offsetX
        self.offsetY = offsetY
        self.mytitle = title
        try:
            minY = int(miny)
            maxY = int(minx)
            self.title(title)
            self.root = root
        except ValueError :
            print(f'Error: calling dynamic plot function')
        self.incoming = 0

        fig, ax = plt.subplots()
        self.data = np.zeros(50)  # Initial data array with 50 zeros
        self.plot, = ax.plot(self.data)
        tk.Label(self, font=("Courier", 12), text=title).pack(pady=5)
        ax.set_ylim(minY, maxY)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.ax = ax
        self.cid = fig.canvas.mpl_connect('draw_event', self.draw)
        self.overrideredirect(True)  # Remove window decorations
        
        if(str(self.mytitle).find('CPU') > -1):
            thread = threading.Thread(target=self.CPUUsageThread)
            thread.start()
        else:
            thread = threading.Thread(target=self.memUsageThread)
            thread.start()
        self.minimize_event = threading.Event()

        self.update_data()

    def minimize(self):
        self.minimize_event.set()

    def maximize(self):
        self.minimize_event.clear()

    def CPUUsageThread(self):
        event = threading.Event()
        while not self.breakout[0]:
            value = psutil.cpu_percent(interval=self.graph_update_rate, percpu=False)
            if value < 0:
                pass
            else:    
                self.addPoint(value)
            event.wait(self.graph_update_rate)

    def memUsageThread(self):
        event = threading.Event()
        while not self.breakout[0]:
            memusage = self.get_memory_info()['Usage %']
            self.addPoint(memusage)
            event.wait(self.graph_update_rate)

    def get_memory_info(self):
        # Retrieve information about memory usage
        virtual_memory = psutil.virtual_memory()
        
        # Memory information in bytes
        total_memory = float(virtual_memory.total) // math.pow(2,30)
        available_memory = float(virtual_memory.available) // math.pow(2,30)
        used_memory = float(virtual_memory.used) // math.pow(2,30)
        percent_memory_used = float(virtual_memory.percent)
        
        return {
            "Total": total_memory,
            "Available": available_memory,
            "Used": used_memory,
            "Usage %": percent_memory_used
        }
        
    def draw(self, event):
        pass  # No need to redraw unless data changes

    def generate_color_arr(start, end):
        color_arr = {}
        for value in range(end + 1):
            start_val = hex(int(start, 16))[2:].zfill(2)
            if value < int(start, 16) or value > 100:
                continue
            if value == int(start, 16):
                increment_value = (value - start) / (end - start + 1) * 255
                end_val = hex(int(end, 16))[2:].zfill(2)
            else:
                end_val = hex((int(end, 16)))[2:].zfill(2)
            color_arr[value] = f"#{start_val}{increment_value:.2f}{end_val}"
        return color_arr
    
    def update_data(self):
        self.onResize()
        if self.newDataReady:
            color_map = {
                0: '#22ff00',
                25: '#77bb00', 
                50: '#bb7700', 
                95: '#FF0000'
            }
            self.newDataReady = False
            if len(self.data) > 50:
                shifted_data = self.data[:len(self.data)-1]
                new_data = np.insert(shifted_data, 0, self.incoming)
            else:
                new_data = np.insert(self.data, 0, self.incoming)
            
            # Update self.data with the new data
            self.data = new_data
            x_vals = np.arange(len(self.data))
            y_vals = self.data
            self.plot.set_data(x_vals, y_vals)
            self.plot.set_color(color_map.get(int(self.incoming // 25 * 25), 'red'))
            # self.plot.set_color(color_map.get(int(self.incoming // 25 * 25), 'red'))
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        
        # Schedule the next update
        self.after(int(self.graph_update_rate * 1000), self.update_data)  # Update every 100ms

    def addPoint(self, incoming):
        self.incoming = incoming
        self.newDataReady = True

    def updatePosition(self,offsetX, offsetY, baseX, baseY, baseH):
        width = 220
        height = int(baseH / 2) - 20
        x = baseX + 20 + offsetX
        y = baseY + 20 + offsetY

        def reposition():
            self.geometry(f"{width}x{height}+{x}+{y}")

        self.root.after(0, reposition)

    def onResize(self):
        if self.minimize_event.is_set():
            self.canvas.get_tk_widget().pack_forget()
            self.withdraw()
        else:
            self.deiconify()
            self.lift()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            