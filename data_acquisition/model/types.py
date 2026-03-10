from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    timestamp_ms: float
    pv0_v: float
    pv1_v: float
    pv2_v: float
    pv3_v: float
    roll_deg: float
    pitch_deg: float
    yaw_deg: float

