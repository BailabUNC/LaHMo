import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

from decompressor import decompress_gz

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Load and denoise pv.')
    parser.add_argument('-c', '--category',
                        help='The category of the file')
    parser.add_argument('-l', '--label',
                        help='The filename of the photovoltage data')
    parser.add_argument('-d', '--delay',
                        help='Delay between two instruments, default 1',
                        default=0.0, type=float)
    parser.add_argument('-s', '--start',
                        help='Start time',
                        default=0.0, type=float)
    parser.add_argument('-e', '--end',
                        help='End time',
                        default=60.0, type=float)
    parser.add_argument('-ts',
                        help='Interval, has downsampled from original data',
                        default=0.0001, type=float)
    parser.add_argument('-sr', '--skiprow',
                        help='Number of rows needs to skip in the original data',
                        default=7, type=int)

    return parser.parse_args()

def pv_det_sea(pv, fs, trend_len_s=2., denoise_len_s=0.25):
    """Detrend the photovoltage with seasonal decompose
    Args:
        pv (array_like): photovoltage values
        fs (int): sampling frequency
        trend_len_s (float, optional): Detrend window length for extracting baseline shift. Defaults to 2.
        denoise_len_s (float, optional): Detrend window length for high-frequency noises. Defaults to 0.25.

    Returns:
        array_like: The detrended signal
    """

    dt1 = seasonal_decompose(pv,
                             model='additive',
                             extrapolate_trend='freq',
                             period=int(denoise_len_s*fs))
    dt2 = seasonal_decompose(pv,
                             model='additive',
                             extrapolate_trend='freq',
                             period=int(trend_len_s*fs))
    return dt1.trend-dt2.trend

def audio_det_sea(audio, sr, trend_len_s=2.):
    """Detrend the audio captured by powerlab
    Args:
        audio (array_like): audio values (in the unit of mV)
        fs (int): sampling frequency
        trend_len_s (float, optional): Detrend window length for extracting baseline shift. Defaults to 2.

    Returns:
        array_like: The detrended audio
    """
    dt = seasonal_decompose(audio,
                            model='additive',
                            extrapolate_trend='freq',
                            period=int(trend_len_s)*sr)
    return audio-dt.trend

def pv_read(args):
    # read in photovoltage
    category = args.category
    label = args.label
    delay_s = args.delay
    start_s = args.start
    end_s = args.end
    ts = args.ts
    skip = args.skiprow
    time, pv, fs = decompress_gz(category=category,
                                 label=label,
                                 delay_o_s=delay_s,
                                 start_s=start_s,
                                 end_s=end_s,
                                 ts=ts,
                                 skip=skip)
    return time, pv, fs

def draw(args):
    # draw detrended pv
    time, pv, fs = pv_read(args)
    pv_det = pv_det_sea(pv, fs,
                        trend_len_s=2,
                        denoise_len_s=0.01)

    fig, _ = plt.subplots(212)
    ax1 = fig.add_subplot(211)
    ax1.plot(time, pv)
    ax2 = fig.add_subplot(212)
    ax2.plot(time, pv_det)
    plt.show()

def main():
    args = parse_args()
    draw(args)

if __name__ == '__main__':
    main()
