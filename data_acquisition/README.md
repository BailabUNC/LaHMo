# LaHMo BLE Data Acquisition (Desktop)

This folder contains a local desktop app that uses **bleak** to scan/connect to BLE devices (including **LaHMo2**) and plots the incoming stream in real time while logging to disk.

## Run

```bash
python -m pip install -r requirements.txt
python -m data_acquisition.app
```

## LaHMo2 defaults

- **Service UUID**: `12fb95d1-4954-450f-a82b-802f71541562`
- **Notify characteristic UUID**: `67136980-20d0-4711-8b37-3acd0fec8e7f`

The firmware sends notifications as a UTF-8 string:

`timestamp_ms,pv0_V,pv1_V,pv2_V,pv3_V,roll_deg,pitch_deg,yaw_deg`

