"""Original paired-input seed, hash and generation rules."""

import hashlib
import json
import random

PAIRED_DISTRIBUTIONS=("paired_shuffled","paired_sorted","paired_reversed")


def input_seed(master: int, distribution: str, size: int, sample: int) -> int:
    key = f"sorting-v1:{master}:{distribution}:{size}:{sample}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")


def input_hash(values: tuple[int, ...]) -> str:
    payload = json.dumps(values, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def paired_workload(master: int, distribution: str, size: int, sample: int) -> tuple[tuple[int, ...], dict]:
    """Same distinct integer values in three orders; no change to legacy generators."""
    if distribution not in PAIRED_DISTRIBUTIONS or size < 0 or sample < 0:
        raise ValueError("Invalid paired workload")
    base_seed = input_seed(master, "paired_base_v1", size, sample)
    shuffle_seed = input_seed(master, "paired_shuffle_v1", size, sample)
    ascending = tuple(sorted(random.Random(base_seed).sample(range(-10 * size, 10 * size + 1), size)))
    if distribution == "paired_sorted":
        values = ascending
    elif distribution == "paired_reversed":
        values = tuple(reversed(ascending))
    else:
        values = list(ascending)
        random.Random(shuffle_seed).shuffle(values)
        values = tuple(values)
    return values, {
        "input_seed": base_seed, "shuffle_seed": shuffle_seed,
        "pair_id": f"{master}:{size}:{sample}",
        "multiset_sha256": input_hash(ascending),
    }
