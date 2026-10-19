"""Measured copying Bubble Sort with early exit."""

from collections.abc import Sequence


def bubble_sort(values: Sequence[int]) -> list[int]:
    data = list(values)
    for end in range(len(data) - 1, 0, -1):
        swapped = False
        for i in range(end):
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
        if not swapped:
            break
    return data
