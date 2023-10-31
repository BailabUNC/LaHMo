import threading
import serial
import time
from datetime import datetime
import csv
from collections import deque
import itertools

import numpy as np
import matplotlib as mpl
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.widgets as widgets

class SerialPlotter:
    def __init__(self, port, baudrate=115200, max_len=500, plot_interval=0.001, csv_filename=None):
        self.ser = serial.Serial(port=port, baudrate=baudrate)
        self.max_len = max_len
        self.plot_interval = plot_interval
        self.csv_filename = csv_filename

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

        # Data writing 
        if self.csv_filename:
            self.csvfile = open(self.csv_filename, 'a+', newline='')
            self.csv_writer = csv.writer(self.csvfile)
        
        
    def start(self):
        # background thread
        self._serial_thread.start()

        # start animation
        self._animation = FuncAnimation(self._fig, self._update_plots, interval=self.plot_interval, cache_frame_data=False)
        
    def stop(self):
        self._stop_event.set()
        self._serial_thread.join()
        if self.csvfile:
            self.csvfile.close()
    
    def _read_serial(self):
        while not self._stop_event.is_set():
        # Read data from serial port
            try:
                serial_byte = self.ser.readline()
                serial_line = serial_byte.decode('utf-8').strip()

                split_strings = serial_line.split('\t')

                timestamp_string = split_strings[0]
                photovoltage0_string = split_strings[1]
                photovoltage1_string = split_strings[2]
                photovoltage2_string = split_strings[3]
                photovoltage3_string = split_strings[4]
                roll_string = split_strings[5]
                pitch_string = split_strings[6]
                yaw_string = split_strings[7]

            except UnicodeDecodeError:
                continue
            except IndexError:
                continue
        
            if len(split_strings) != 8: # incomplete line
                print(len(split_strings))
                continue

            if self._last_timestamp == int(timestamp_string):
                continue
        
            self._last_timestamp = int(timestamp_string)
            self._last_pv0 = float(photovoltage0_string)
            self._last_pv1 = float(photovoltage1_string)
            self._last_pv2 = float(photovoltage2_string)
            self._last_pv3 = float(photovoltage3_string)
            self._last_roll = float(roll_string)
            self._last_pitch = float(pitch_string)
            self._last_yaw = float(yaw_string)
            
            self.timestamps.append(self._last_timestamp)
            self.pv0.append(self._last_pv0)
            self.pv1.append(self._last_pv1)
            self.pv2.append(self._last_pv2)
            self.pv3.append(self._last_pv3)
            self.roll.append(self._last_roll)
            self.pitch.append(self._last_pitch)
            self.yaw.append(self._last_yaw)
                    
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
        
    def _on_stop_button_clicked(self, event):
        self.stop()
        plt.close(self._fig)

if __name__ == '__main__':
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
    
    serial_plotter = SerialPlotter('COM8', max_len=100, csv_filename='../dataset/ble_test/test-'+time_str+'.csv')
    
    serial_plotter.start()
    plt.show(block=True)

    # input('Press Enter to stop...\n')
    serial_plotter.stop()