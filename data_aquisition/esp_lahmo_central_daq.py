import threading
import serial
import time
from datetime import datetime
import csv
from collections import deque
import argparse
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.widgets as widgets

class SerialPlotter:
    def __init__(self, port, baudrate=115200, max_len=500, plot_interval=0.001, csv_filename=None, conn_timeout=5):
        self.ser = serial.Serial(port=port, baudrate=baudrate)
        self.max_len = max_len
        self.plot_interval = plot_interval
        self.conn_timeout = conn_timeout

        # Data export
        self.csv_filename = csv_filename
        self.csvfile = None
        self.csv_writer = None

        # Initialize containers
        self.timestamps = deque([], maxlen=self.max_len)
        self.pv0 = deque([], maxlen=self.max_len)
        self.pv1 = deque([], maxlen=self.max_len)
        self.pv2 = deque([], maxlen=self.max_len)
        self.pv3 = deque([], maxlen=self.max_len)
        self.roll = deque([], maxlen=self.max_len)
        self.pitch = deque([], maxlen=self.max_len)
        self.yaw = deque([], maxlen=self.max_len)
        
        self._last_timestamp = 0
        self._last_pv0 = 0
        self._last_pv1 = 0
        self._last_pv2 = 0
        self._last_pv3 = 0
        self._last_roll = 0
        self._last_pitch = 0
        self._last_yaw = 0

        # Initialize plots
        self._fig, self._axes = plt.subplots(7, 1, sharex=True, figsize=[10, 10])
        self._line0, = self._axes[0].plot(self.timestamps, self.pv0)
        self._line1, = self._axes[1].plot(self.timestamps, self.pv1)
        self._line2, = self._axes[2].plot(self.timestamps, self.pv2)
        self._line3, = self._axes[3].plot(self.timestamps, self.pv3)
        
        self._liner, = self._axes[4].plot(self.timestamps, self.roll)
        self._linep, = self._axes[5].plot(self.timestamps, self.pitch)
        self._liney, = self._axes[6].plot(self.timestamps, self.yaw)

        for ii, ax in enumerate(self._axes):
            if ii < 4:
                ax.set_ylabel('PV (mV)')
            elif ii == 4:
                ax.set_ylabel('Roll ($\circ$)')
            elif ii == 5:
                ax.set_ylabel('Pitch ($\circ$)')
            elif ii == 6:
                ax.set_ylabel('Yaw ($\circ$)')
                ax.set_xlabel('Time (ms)')
        
        self._colors = pl.cm.tab10(np.linspace(0, 1, 7))
        
        # Start background thread for reading data from serial port
        self._serial_thread = threading.Thread(target=self._read_serial)
        self._stop_event = threading.Event()

        # Initialize a button for stopping the data acquisition
        self._stop_button_ax = self._fig.add_axes([0.85, 0.025, 0.1, 0.04])
        self._stop_button = widgets.Button(self._stop_button_ax, 'Stop')
        self._stop_button.on_clicked(self._on_stop_button_clicked)
        
    def _on_stop_button_clicked(self, event):
        self.stop()

    def start(self):
        # background thread
        self._serial_thread.start()

        # start animation
        self._animation = FuncAnimation(self._fig, self._update_plots, interval=self.plot_interval, cache_frame_data=False)
        
    def stop(self):
        self._stop_event.set()
        plt.close(self._fig)

        if threading.current_thread() != self._serial_thread:
            self._serial_thread.join()
        if self.csvfile:
            self.csvfile.close()
            self.csvfile = None
    
    def _parse_serial_line(self, serial_line):
        try:
            split_strings = serial_line.split('\t')
            if len(split_strings) != 8:
                return False  # Incomplete line
            
            data_keys = [
                '_last_timestamp',
                '_last_pv0',
                '_last_pv1',
                '_last_pv2',
                '_last_pv3',
                '_last_roll',
                '_last_pitch',
                '_last_yaw'
                ]
            for i, key in enumerate(data_keys):
                setattr(self, key, float(split_strings[i]))

            return True
        
        except ValueError:
            return False

    def _read_serial(self):
        # timestamp to record the first disconnect (first occurrance of UnicodeDecodeError)
        disconn_start_time = None
        
        while not self._stop_event.is_set():
        # Read data from serial port
            try:
                serial_byte = self.ser.readline()
                serial_line = serial_byte.decode('utf-8').strip()

                if not self._parse_serial_line(serial_line):
                    continue

                disconn_start_time = None # reset the disconnect counter

            except UnicodeDecodeError:
                if not disconn_start_time:
                    disconn_start_time = time.perf_counter()
                elif time.perf_counter() - disconn_start_time > self.conn_timeout:
                    print('Timeout connecting to the given LaHMo.')
                    self.stop()
                    break
                continue

            except IndexError:
                continue
            
            self.timestamps.append(self._last_timestamp)
            self.pv0.append(self._last_pv0)
            self.pv1.append(self._last_pv1)
            self.pv2.append(self._last_pv2)
            self.pv3.append(self._last_pv3)
            self.roll.append(self._last_roll)
            self.pitch.append(self._last_pitch)
            self.yaw.append(self._last_yaw)
            
            if not self.csvfile and self.csv_filename:
                self.csvfile = open(self.csv_filename, 'a+', newline='')
                self.csv_writer = csv.writer(self.csvfile)

            # Write to csv
            if self.csv_filename:
                self.csv_writer.writerow([np.around(self._last_timestamp, 3),
                                          self._last_pv0,
                                          self._last_pv1,
                                          self._last_pv2,
                                          self._last_pv3,
                                          self._last_roll,
                                          self._last_pitch,
                                          self._last_yaw])
                self.csvfile.flush()
            
    def _update_plots(self, frame):
        # Update plot data
        self._line0.set_xdata(self.timestamps)
        self._line0.set_ydata(self.pv0)
        self._line1.set_xdata(self.timestamps)
        self._line1.set_ydata(self.pv1)
        self._line2.set_xdata(self.timestamps)
        self._line2.set_ydata(self.pv2)
        self._line3.set_xdata(self.timestamps)
        self._line3.set_ydata(self.pv3)
        
        self._liner.set_xdata(self.timestamps)
        self._liner.set_ydata(self.roll)
        self._linep.set_xdata(self.timestamps)
        self._linep.set_ydata(self.pitch)
        self._liney.set_xdata(self.timestamps)
        self._liney.set_ydata(self.yaw)
        
        for ax in self._axes:
            ax.relim()
            ax.autoscale_view()
        
        # Set line color
        self._line0.set_color(self._colors[0])
        self._line1.set_color(self._colors[1])
        self._line2.set_color(self._colors[2])
        self._line3.set_color(self._colors[3])
        self._liner.set_color(self._colors[4])
        self._linep.set_color(self._colors[5])
        self._liney.set_color(self._colors[6])
        
        
        return self._line0, self._line1, self._line2, self._line3, self._liner, self._linep, self._liney
        
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read serial data from specific serial port.')
    parser.add_argument('--port', metavar='P', type=str, help='The serial port to read from.')

    args = parser.parse_args()
    if not args.port:
        print("No port specified.")
        sys.exit(-1)
    else:
        port = args.port

    mpl.rcParams['font.family'] = 'arial'
    mpl.rcParams['font.size'] = 14

    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    hour = now.strftime('%H')
    minute = now.strftime('%M')
    second = now.strftime('%S')
    time_str = '-'.join((year, month, day, hour, minute, second))
    
    serial_plotter = SerialPlotter(port, max_len=100, csv_filename=f'dataset/ble_test/test-{time_str}.csv')
    
    serial_plotter.start()
    plt.show(block=True)

    serial_plotter.stop()