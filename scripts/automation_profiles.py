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
