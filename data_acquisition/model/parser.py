from __future__ import annotations

from .types import Sample


def parse_lahmo2_csv_line(line: str) -> Sample | None:
    """
    Parse LaHMo2 notification payload.

    Expected format (UTF-8 text):
      timestamp_ms,pv0_V,pv1_V,pv2_V,pv3_V,roll_deg,pitch_deg,yaw_deg
    """
    parts = line.strip().split(",")
    if len(parts) != 8:
        return None
    try:
        values = [float(p) for p in parts]
    except ValueError:
        return None
    return Sample(
        timestamp_ms=values[0],
        pv0_v=values[1],
        pv1_v=values[2],
        pv2_v=values[3],
        pv3_v=values[4],
        roll_deg=values[5],
        pitch_deg=values[6],
        yaw_deg=values[7],
    )

