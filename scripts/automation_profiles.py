"""Resource budgets shared by the updater and its systemd installer."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BuildProfile:
    jobs: int
    memory_gib: int
    hours: int


BUILD_PROFILES = {
    'conservative': BuildProfile(jobs=2, memory_gib=16, hours=36),
    'standard': BuildProfile(jobs=8, memory_gib=32, hours=12),
}


def available_memory_kib(meminfo):
    for line in meminfo.read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])
    raise ValueError('MemAvailable missing from meminfo')


def select_profile(mode, memory_kib):
    if mode != 'auto':
        return mode
    if memory_kib >= BUILD_PROFILES['standard'].memory_gib * 1024**2:
        return 'standard'
    # Keep recovery and completed candidate work reachable below the build floor.
    return 'conservative'
