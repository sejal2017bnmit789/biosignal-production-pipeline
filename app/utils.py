import math
import numpy as np
import pyedflib
from scipy.signal import resample, butter, filtfilt, find_peaks

def read_file(file_path: str):
    all_signals = []
    f = pyedflib.EdfReader(file_path)
    n = f.signals_in_file
    
    signals = []
    for i in range(n):
        signal = f.readSignal(i)
        signals.append(signal)
    all_signals.append(signals)
    f.close()
    
    sound_signals = [signals_array[18] for signals_array in all_signals]
    return sound_signals[0]

def resample_signal(sound_signals: np.ndarray):
    original_sr = 48000
    secs = int(len(sound_signals) / original_sr) 
    samps = secs * 100    # Downsample to 100 Hz
    audio_data = resample(sound_signals, samps)
    sr = 100
    return audio_data, sr

def bandpass_filter(audio_signal: np.ndarray, sr: int):
    nyquist = 0.5 * sr
    f1 = 0.1 / nyquist
    f2 = 1.5 / nyquist
    b, a = butter(1, [f1, f2], btype='band')
    filtered_audio = filtfilt(b, a, audio_signal) 
    return filtered_audio

def calculate_breathing_rate(audio_signal: np.ndarray, sr: int = 100):
    epoch_duration = 60
    epoch_length = epoch_duration * sr
    num_epochs = int(np.ceil(len(audio_signal) / epoch_length))
    breathing_rates = []

    for i in range(num_epochs):
        start = i * epoch_length
        end = min((i + 1) * epoch_length, len(audio_signal))
        epoch_signal = audio_signal[start:end]

        # Moving average smoothing
        window_size = int(0.1 * sr)
        moving_avg = np.convolve(epoch_signal, np.ones(window_size)/window_size, mode='same')

        # Thresholding and peak detection
        threshold = np.percentile(moving_avg, 80)
        peaks, _ = find_peaks(moving_avg, height=threshold, distance=sr * 2.3)

        y = np.array(peaks)
        r_ts = y / sr
        intervals = np.diff(r_ts)
        
        if len(intervals) == 0:
            breathing_rates.append(0)
            continue
            
        avg_breath_period_1 = np.mean(intervals)
        breathing_rate = 60 / avg_breath_period_1
                  
        if math.isnan(breathing_rate):
            breathing_rates.append(0)        
        else:
            breathing_rates.append(round(breathing_rate))  
          
    return breathing_rates

def process_pipeline_from_array(raw_signal_array: list[float]) -> list[int]:
    """
    Orchestration layer: Takes raw audio array data directly from the API endpoint,
    resamples it, filters it, and evaluates breathing rate.
    """
    signal_np = np.array(raw_signal_array)
    
    # 1. Resample
    audio_data, sr = resample_signal(signal_np)
    
    # 2. Filter
    filtered_audio = bandpass_filter(audio_data, sr)
    
    # 3. Calculate Rate
    rates = calculate_breathing_rate(filtered_audio, sr)
    return rates
