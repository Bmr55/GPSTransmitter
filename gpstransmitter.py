import os, sys, time, datetime, logging, json
from gps3 import agps3
from websocket import create_connection

NO_DATA_TIMEOUT = 0.1
NEW_DATA_TIMEOUT = 1

def load_config():
    script_dir = os.path.dirname(__file__)
    with open(os.path.join(script_dir, "config.json"), "r") as fp:
        return json.load(fp)

def handle_args(args):
    debug_arg = args[1]
    try:
        m = debug_arg.split("=")[1]
        if m.lower() == "true":
            return True
        elif m.lower() == "false":
            return False
        else:
            sys.exit()
    except:
        print("Invalid Argument. Use debug={true|false}")
        sys.exit()

def setup_gpsd_socket():
    gpsd_socket = agps3.GPSDSocket()
    gpsd_socket.connect(host="localhost", port=2947)
    gpsd_socket.watch()
    #logging.info(str(datetime.datetime.now()) + ": GPSDSocket created")
    data_stream = agps3.DataStream()
    #logging.info(str(datetime.datetime.now()) + ": DataStream acquired")
    return gpsd_socket, data_stream

def connect(ws_url, debug_mode):
    ws = None
    connected = False
    while not connected:
        try:
            ws = create_connection(ws_url)
            connected = True
            if debug_mode:
                print("Websocket Connection Established")
            #logging.info(str(datetime.datetime.now()) + ": Websocket connection established")
        except Exception as e:
            if debug_mode:
                print("Websocket Connection Failed. Retrying...")
            #logging.error(str(datetime.datetime.now()) + ": Websocket Connection Failed: " + type(e).__name__ + ": " + str(e))
            time.sleep(5)
    return ws

def create_payload(deviceid, ts, lat, lon, alt, speed):
    if alt == "n/a":
        alt = -1.0
    if speed == "n/a":
        speed = -1.0

    tpv = {
        "deviceid":deviceid,
        "ts":ts,
        "lat":lat,
        "lon":lon,
        "speed":speed,
        "alt":alt
    }

    return { "messageType": "tpvupdate", "tpv":tpv }

def main(args):
    config = load_config()

    #logging.basicConfig(level=logging.INFO, filename="gpstransmitter.log")

    debug_mode = False
    if len(args) > 1:
        debug_mode = handle_args(args)

    gpsd_socket, data_stream = setup_gpsd_socket()

    if debug_mode:
        print("GPSDSocket created")
        print("DataStream acquired")

    ws = connect(config["websocket_url"], debug_mode)

    try:
        print("Trying to get gps data...")
        for new_data in gpsd_socket:
            #logging.info(str(datetime.datetime.now()) + ": gpsdsocket loop")
            if new_data:
                # unpack data into dict
                data_stream.unpack(new_data)
                # check for valid gps data
                if data_stream.lat != "n/a":
                    payload = create_payload(
                        config["deviceid"],
                        data_stream.time,
                        data_stream.lat,
                        data_stream.lon,
                        data_stream.alt,
                        data_stream.speed
                    )

                    try:
                        ws.send(json.dumps(payload))
                        if debug_mode:
                            print("Payload:")
                            print(str(payload) + "\n")
                            print("Message Sent")
                        #logging.info(str(datetime.datetime.now()) + ": GPS data sent")
                    except Exception as e:
                        if debug_mode:
                            print("Websocket Closed")
                            print(e)
                        #logging.error(str(datetime.datetime.now()) + ": Failed to send GPS data: " + type(e).__name__ + ": " + str(e))
                        ws.close()
                        ws = connect(config["websocket_url"], debug_mode)
                    except:
                        print("Uknown exception")
                        #logging.error(str(datetime.datetime.now()) + ": Unknown exception")
                else:
                    if debug_mode:
                        print("Bad DataStream Data")

            else:
                if debug_mode:
                    print("No new data")
                #logging.info(str(datetime.datetime.now()) + ": No new GPS data available")
                time.sleep(NO_DATA_TIMEOUT)
            time.sleep(NEW_DATA_TIMEOUT)
    except KeyboardInterrupt:
        ws.close()
        gpsd_socket.close()
        print("Terminated via KeyboardInterrupt")

if __name__ == '__main__': main(sys.argv)
