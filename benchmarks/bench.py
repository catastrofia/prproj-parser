"""Benchmark harness for prproj-parser.

Times load() and list_sequences() on generated fixtures, optionally with
cProfile. Usage:
    python bench.py /path/to.prproj [--profile]
"""

import cProfile
import io
import pstats
import sys
import time

sys.path.insert(0, "src")


def bench(path: str, profile: bool = False, repeat: int = 3) -> None:
    from prproj_parser import list_sequences, load

    # Warm-up (imports, bytecode)
    load(path)

    best = min(
        (lambda t0: (load(path), time.perf_counter() - t0)[1])(time.perf_counter())
        for _ in range(repeat)
    )

    t0 = time.perf_counter()
    names = list_sequences(path)
    t_list = time.perf_counter() - t0

    proj = load(path)
    n_clips = sum(len(s.clips) for s in proj.sequences)
    print(
        f"{path}: load={best * 1000:.1f} ms  list_sequences={t_list * 1000:.1f} ms"
        f"  ({len(proj.sequences)} seqs, {n_clips} clips, names={names[:3]}...)"
    )

    if profile:
        prof = cProfile.Profile()
        prof.enable()
        load(path)
        prof.disable()
        buf = io.StringIO()
        stats = pstats.Stats(prof, stream=buf).sort_stats("cumulative")
        stats.print_stats(28)
        print(buf.getvalue())


if __name__ == "__main__":
    path = sys.argv[1]
    bench(path, profile="--profile" in sys.argv)
