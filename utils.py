import numpy as np
import pandas as pd
from scipy import interpolate
from scipy.signal import butter, sosfiltfilt, find_peaks
from sklearn.linear_model import LinearRegression
import torch

# load

def my_expand_yaw(yaw):
    '''Fix yaw jumps from 0 to 360 and/or from 360 to 0'''
    expanded_yaw = []
    previous_val = 0
    offset = 0
    
    for val in yaw:
        diff = val - previous_val
        if diff > 350:
            offset -= 360
        expanded_yaw.append(val + offset)
        previous_val = val

    return np.array(expanded_yaw)

def fix_timestamps(timestamp):
    '''Redo IMU timestamps'''
    return np.around(timestamp)

def load_pv(date, filename):
    path = '/'.join(['..', 'dataset', 'pv', date, filename])
    data = pd.read_csv(path,
                    skiprows=6,
                    delimiter='\t',
                    header=None).to_numpy()
    timestamp = data[:, 0]
    
    c = data[:, 1]
    b = data[:, 2]
    tl = data[:, 3]
    tr = data[:, 4]
    return timestamp, c, b, tl, tr

def load_ori(date, filename, shift):
    path = '/'.join(['..', 'dataset', 'orientation', date, filename])
    data = pd.read_csv(path,
                      skiprows=1+shift,
                      delimiter='\t',
                      header=None).to_numpy()
    timestamp = data[:, 0]-data[0, 0]
    timestamp = fix_timestamps(timestamp)
    y = data[:, 1]
    p = data[:, 2]
    r = data[:, 3]
    
    y = my_expand_yaw(y)
    return timestamp, y, p, r

# preprocessing

def upsample(timestamp, arr, ratio=10):
    f = interpolate.interp1d(timestamp, arr)
    timestamp_upsampled = np.linspace(start=timestamp[0], stop=timestamp[-1], num=int(np.around((len(timestamp)+1)*ratio+1)))
    arr_upsampled = f(timestamp_upsampled)
    return timestamp_upsampled, arr_upsampled

def despike(arr, window_size, threshold):
    pad_size = window_size // 2
    arr_padded = np.pad(arr, pad_size, mode='reflect')
    arr_rolled = np.convolve(arr_padded, np.ones(window_size)/window_size, mode='same')
    spikes = np.abs(arr-arr_rolled[pad_size:-pad_size]) > threshold
    arr_despiked = np.copy(arr)
    arr_despiked[spikes] = arr_rolled[pad_size:-pad_size][spikes]
    return arr_despiked

def detrend(arr, method='linear', fc=1):
    x = np.arange(len(arr)).reshape(-1, 1)
    if method == 'linear':
        model = LinearRegression().fit(x, arr)
        trend = model.predict(x)
        detrended = arr - trend.flatten()
    elif method == 'butter':
        sos = butter(3, fc, btype='lowpass', output='sos', fs=1000/(x[1] - x[0]))
        trend = sosfiltfilt(sos, arr)
        detrended = arr - trend.flatten()
    return detrended

def normalize(arr):
    arr_min = np.min(arr, axis=0)
    arr_max = np.max(arr, axis=0)
    arr_norm = 2*((arr - arr_min) / (arr_max - arr_min)) - 1
    return arr_norm

# slicing and reshaping data

def peak_expand(peaks, n, max):
    expanded_list = []
    for peak in peaks:
        temp_list = list(range(peak-n//2, peak+n//2))
        if all(0 < x < max for x in temp_list):
            expanded_list.append(temp_list) 
    return np.array(expanded_list)

def peak_shift(peaks, shift, n, max):
    shifted_list = []
    for peak in peaks:
        temp_list = list(range(peak-shift-n//2, peak-shift+n//2))
        if all(0 < x < max for x in temp_list):
            shifted_list.append(temp_list)
    return np.array(shifted_list)

def window_stack(data, window_size):
    n_windows = data.shape[0] // window_size
    windowed_data = torch.stack([data[i: i+window_size] for i in range(0, n_windows*window_size, window_size)])
    return windowed_data.transpose(1, 2)

def section_average(all_windows):
    '''shape: [n_window, peak_window]'''
    window_to_keep = np.ones(all_windows.shape[0])
    avg = np.mean(all_windows, axis=0)
    std = np.std(all_windows, axis=0)
    for window_idx, window in enumerate(all_windows):
        for idx, val in enumerate(window):
            if np.abs(val-avg[idx]) > 3*std[idx]:
                window_to_keep[window_idx] = 0
    return window_to_keep
