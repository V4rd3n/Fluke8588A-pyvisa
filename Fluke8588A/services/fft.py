"""FFT of a digitized block, as calculate_FFT of the reference UI_JAWS project (scipy)."""
from dataclasses import dataclass
import numpy as np
from scipy.fftpack import fft, fftfreq

# Names shown by gui_values.DIGI_FFT_WINDOWS
WINDOWS = {
    "Rectangular": np.ones,
    "Hanning": np.hanning,
    "Hamming": np.hamming,
    "Blackman": np.blackman,
}


@dataclass
class FftResults:
    window_name: str
    freqs: np.ndarray
    magnitude_db: np.ndarray
    peak: float
    peak_frequency: float
    thd_dbc: float


def frequencies(n_points: int, sample_rate: float) -> np.ndarray:
    """Frequency axis in Hz of a block of n_points taken at sample_rate (samples/s)."""
    return fftfreq(n_points, 1 / sample_rate)[:n_points // 2]


def calculate_fft(values, freqs, window_name: str) -> tuple[np.ndarray, float, float, float]:
    """
    Spectrum of a block with the window of WINDOWS, freqs from frequencies().
    Returns (magnitude in dB relative to 1 unit rms, peak amplitude in rms,
    peak frequency in Hz, THD in dBc).
    """
    n_points = len(values)
    window = WINDOWS[window_name](n_points)

    # Amplitude correction factor of the window
    ampl_corr = n_points / np.sum(window)

    yf = fft(np.multiply(values, window))[:n_points // 2]
    # Normalized magnitude, transformed to rms
    yf_mag = (ampl_corr / np.sqrt(2)) * np.abs(yf) / (n_points // 2)

    # Search for local maxima by index, to avoid DC and 1/f noise which should be monotonic
    local_max_idxs = np.where((yf_mag[1:-1] > yf_mag[:-2]) & (yf_mag[1:-1] > yf_mag[2:]))[0] + 1
    max_index = local_max_idxs[np.argmax(yf_mag[local_max_idxs])]

    peak_frequency = freqs[max_index]

    # Number of adjacent bins taken into account in the peak amplitude
    n_adj_left = 0
    n_adj_right = 0

    if max_index - n_adj_left < 0:
        n_adj_left = max_index
    if n_adj_right + max_index > n_points:
        n_adj_right = n_points - max_index

    peak_amplitude = np.sqrt(np.sum((yf_mag[max_index - n_adj_left:max_index + n_adj_right + 1]) ** 2))

    indexes = np.arange(max_index * 2, len(yf_mag), max_index)
    harmonics = yf_mag[indexes]

    harmonics_power = np.sum(harmonics * harmonics)

    if harmonics_power == 0:
        thd_dBc = float('-inf')
    elif peak_amplitude == 0:
        thd_dBc = float('inf')
    else:
        # THD relative to the carrier, up to the highest harmonic in the spectrum
        thd_dBc = 10 * np.log10(harmonics_power / (peak_amplitude ** 2))

    magnitude_db = 20 * np.log10(yf_mag)
    return magnitude_db, peak_amplitude, peak_frequency, thd_dBc
