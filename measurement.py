"""Original batch timer/calibrator without workspace tooling."""

import gc
import math
import time


def timed_batch(function, values, expected, calls: int) -> int:
    """Validate the final output outside timing; restore the caller's GC state."""
    enabled = gc.isenabled()
    gc.disable()
    try:
        start = time.perf_counter_ns()
        for _ in range(calls):
            result = function(values)
        elapsed = time.perf_counter_ns() - start
    finally:
        if enabled:
            gc.enable()
    if result != expected:
        raise AssertionError("Timed batch produced an incorrect result")
    return elapsed


def calibrate(function, values, expected, config: dict) -> tuple[int, list[dict]]:
    calls = 1
    trials = []
    while True:
        elapsed = timed_batch(function, values, expected, calls)
        trials.append({"calls": calls, "elapsed_ns": elapsed})
        if elapsed / calls > config["soft_call_limit_seconds"] * 1e9:
            raise TimeoutError("Calibration exceeded the soft per-call limit; no hard interruption")
        if elapsed >= config["target_batch_ns"] or calls >= config["max_calls"]:
            return calls, trials
        factor = max(2, min(10, math.ceil(config["target_batch_ns"] / max(elapsed, 1))))
        calls = min(config["max_calls"], calls * factor)
