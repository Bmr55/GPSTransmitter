# GPSTransmitter
A python program using gps3 and websockets to transmit GPS data to a server

## Install Dependencies
``` pip3 install -r requirements.txt ```

## config.json
Use this file to configure your unique deviceid and websocket server location

## Example Transmission Message 
```json
{
  "messageType": "TpvUpdate",
  "tpv": {
    "deviceid": "custom-deviceid",
    "ts": "2021-03-30T12:18:17",
    "lat": 40.713009,
    "lon": -74.013168,
    "speed": 8.9408,
    "alt": 10.0584
  }
}
```
