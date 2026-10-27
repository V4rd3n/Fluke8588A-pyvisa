"""Statistics of the readings, updated one reading at a time."""
import math


class RunningStatistics:
    """
    Count, mean, standard deviation and standard deviation of the mean of a
    series of values, updated in O(1) per value (Welford's algorithm).

    Welford keeps the deviations from the running mean instead of the sum of
    the squares: with DMM readings (e.g. 10 V +- a few uV) the sum of the
    squares would lose the digits the standard deviation is made of.
    """

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self._count = 0
        self._last = None
        self._mean = 0.0
        self._m2 = 0.0  # sum of the squared deviations from the mean

    def add(self, value: float) -> None:
        self._count += 1
        self._last = value
        delta = value - self._mean
        self._mean += delta / self._count
        self._m2 += delta * (value - self._mean)

    @property
    def count(self) -> int:
        return self._count

    @property
    def last(self) -> float | None:
        return self._last

    @property
    def mean(self) -> float | None:
        return self._mean if self._count > 0 else None

    @property
    def stdev(self) -> float | None:
        """Sample standard deviation (N - 1), None with less than 2 values."""
        if self._count < 2:
            return None
        return math.sqrt(self._m2 / (self._count - 1))

    @property
    def stdev_mean(self) -> float | None:
        """Standard deviation of the mean: stdev / sqrt(N), None with less than 2 values."""
        stdev = self.stdev
        if stdev is None:
            return None
        return stdev / math.sqrt(self._count)
