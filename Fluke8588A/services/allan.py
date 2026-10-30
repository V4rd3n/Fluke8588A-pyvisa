"""Overlapping Allan deviation of a series of readings (allantools)."""
import allantools
import numpy as np

# Fewest readings for allantools
MIN_READINGS = 3


def overlapping_adev(values, rate: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Overlapping Allan deviation of readings taken at rate (readings/s), as
    allantools.oadev(values, rate, data_type="freq", taus="all").
    Returns (tau in s, adev in the unit of the readings).
    """
    values = np.asarray(values, dtype=float)
    if len(values) < MIN_READINGS or rate <= 0:
        return np.array([]), np.array([])
    # "all" is O(N^2) (300k readings take 2 min): computed in an AllanThread
    tau_out, adev, _, _ = allantools.oadev(values, rate=rate, data_type="freq", taus="all")
    return tau_out, adev


def mean_rate(times) -> float:
    """Readings/s from their times, 1 / mean of the time differences."""
    if len(times) < 2 or times[-1] <= times[0]:
        return 0.0
    return (len(times) - 1) / (times[-1] - times[0])
