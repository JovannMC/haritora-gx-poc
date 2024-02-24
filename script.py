# Hey welcome to the project, by JovannMC (and a bit too much of ChatGPT)
# I would recommend using a program like RealTerm to capture the serial data, and then "echo" the data to the server.

import socket
import struct
import argparse
import logging
import json
from json.decoder import JSONDecodeError
from datetime import datetime

# Initialize logger and debug mode variable
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
debug_mode = False

# Echo the data to these details for the program to interpret, recommended to use RealTerm.
HOST = '127.0.0.1'
PORT = 9876

# There's gotta be a better way to do this. Read below for more info.
r0_prev_main_button_press_count = 0
r0_prev_sub_button_press_count = 0
r1_prev_main_button_press_count = 0
r1_prev_sub_button_press_count = 0


class DecodeError(Exception):
    pass


class Rotation:
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w


class Gravity:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


#
# Server stuff
# The code to start a local server to receive the serial data from and the handling of it.
#

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        logging.info(f'Server listening on {HOST}:{PORT}')
        while True:
            client_socket, client_address = server_socket.accept()
            logging.info(f'Connection established from {client_address}')
            handle_client(client_socket)


def handle_client(client_socket):
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            process_data(data)


def process_data(data):
    lines = data.strip().split(b'\n')
    if debug_mode:
        # Print raw data received by server
        logging.debug(f"Processed lines: {lines}")
    for line in lines:
        parts = line.split(b':', 1)
        if len(parts) == 2:
            label, data = parts
            """if b'X' in label:
                # IMU tracker data
                tracker_number = int(label.split(b'X')[-1])
                process_tracker_data(data, tracker_number)"""
            if b'a' in label:
                # Other tracker data
                tracker_number = int(label.split(b'a')[-1])
                process_other_tracker_data(data, tracker_number)
            """elif b'r' in label:
                # Tracker button info
                tracker_number = int(label.split(b'r')[-1])
                process_button_data(data, tracker_number)
            elif b'v' in label:
                # Tracker battery info
                tracker_number = int(label.split(b'v')[-1])
                process_battery_data(data, tracker_number)
            else:
                logging.info(f"Unknown label: {label}")
                logging.info(f"Unknown label's data: {data.decode('utf-8')}")"""


#
# Tracker data
# This is obviously the IMU tracking data, the juicy stuff. Ankle motion data also included (if enabled).
# Can be used to forward to other software such as SlimeVR's server!
# Rotation has: x, y, z, w
# Gravity has: x, y, z
#

def process_ankle_motion_data(data):
    # Process ankle motion data
    # TODO: see how to process the data, but we have it here
    logging.info(f"Processing ankle motion data: {data}")


def process_tracker_data(data, tracker_num):
    try:
        if data[-2:] == b'==' and len(data) == 24:
            # Other trackers
            try:
                rotation, gravity = decode_imu_packet(data)
                logging.info(f'Tracker {tracker_num} rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w})')
                logging.info(f'Tracker {tracker_num} gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
            except DecodeError as e:
                logging.info(f"Error decoding tracker {tracker_num} IMU packet:", e)
        else:
            # Ankle trackers
            if data and len(data) == 24:
                decoded_data = data.decode('utf-8')

                ankle_motion_data = decoded_data[-2:]
                process_ankle_motion_data(ankle_motion_data)

                imu_data = decoded_data[:-2]

                try:
                    rotation, gravity = decode_imu_packet(imu_data.encode('utf-8'))
                    logging.info(f'Tracker {tracker_num} rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w})')
                    logging.info(f'Tracker {tracker_num} gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
                except DecodeError:
                    logging.info(f'Error decoding tracker {tracker_num} IMU packet: {decoded_data}')
            else:
                logging.info(f"Invalid or short data received. Skipping processing of data: {data}")

    except DecodeError:
        logging.info("Error decoding data:", data)


#
# Other tracker data
# Currently unsure what other data a0/a1 could represent other than trying to find the trackers,
# I see other values for it too. This could also be used to report calibration data when running the
# calibration through the software. Also, could be if the tracker is just turned on/off.
#

def process_other_tracker_data(data, tracker_num):
    decoded_data = data.decode('utf-8')
    if decoded_data.strip() == '7f7f7f7f7f7f':
        logging.info(f"Searching for tracker {tracker_num}...")
    else:
        logging.info(f"Other tracker {tracker_num} data processed: {decoded_data}")


def process_a1_data(data):
    decoded_data = data.decode('utf-8')
    if decoded_data.strip() == '7f7f7f7f7f7f':
        logging.info("Searching for tracker 2...")
    else:
        logging.info(f"Other A1 data processed: {decoded_data}")


#
# Tracker button data
# Here we're processing the button pressed, the 7th/10th character in the decoded data is the
# amount of times the main/sub buttons were pressed respectively.
#

def process_button_press(tracker_num, main_button_press_count, sub_button_press_count, prev_main_button_press_count,
                         prev_sub_button_press_count):
    if main_button_press_count != prev_main_button_press_count:
        logging.info(f"Tracker {tracker_num} main button pressed. Pressed {main_button_press_count + 1} times.")
        prev_main_button_press_count = main_button_press_count
    if sub_button_press_count != prev_sub_button_press_count:
        logging.info(f"Tracker {tracker_num} sub button pressed. Pressed {sub_button_press_count + 1} times.")
        prev_sub_button_press_count = sub_button_press_count
    return prev_main_button_press_count, prev_sub_button_press_count


def process_button_data(data, tracker_num):
    decoded_data = data.decode('utf-8')

    if tracker_num == 0:
        global r0_prev_main_button_press_count, r0_prev_sub_button_press_count
        main_button_press_count = int(decoded_data[6], 16)  # 7th character (0-indexed)
        sub_button_press_count = int(decoded_data[9], 16)  # 10th character (0-indexed)

        r0_prev_main_button_press_count, r0_prev_sub_button_press_count = process_button_press(
            tracker_num, main_button_press_count, sub_button_press_count, r0_prev_main_button_press_count,
            r0_prev_sub_button_press_count)

    elif tracker_num == 1:
        global r1_prev_main_button_press_count, r1_prev_sub_button_press_count
        main_button_press_count = int(decoded_data[6], 16)  # 7th character (0-indexed)
        sub_button_press_count = int(decoded_data[9], 16)  # 10th character (0-indexed)

        r1_prev_main_button_press_count, r1_prev_sub_button_press_count = process_button_press(
            tracker_num, main_button_press_count, sub_button_press_count, r1_prev_main_button_press_count,
            r1_prev_sub_button_press_count)


#
# Tracker battery info
# This contains the information about of the
# Can be used to forward to other software such as SlimeVR's server!
#

def process_battery_data(data, tracker_num):
    try:
        battery_info = json.loads(data)
        print(f"Tracker {tracker_num} remaining: {battery_info.get('battery remaining')}%")
        print(f"Tracker {tracker_num} voltage: {battery_info.get('battery voltage')}")
        print(f"Tracker {tracker_num} Status: {battery_info.get('charge status')}")
    except JSONDecodeError as e:
        print(f"Error processing battery data: {e}")


#
# Decoding IMU packets
# The logic to decode the IMU packet received by the dongle. Thanks to sim1222's project for helping with the math :p
# https://github.com/sim1222/haritorax-slimevr-bridge/
#

def decode_imu_packet(data):
    try:
        if len(data) < 14:
            raise DecodeError("Too few bytes to decode IMU packet")

        rotation_x, rotation_y, rotation_z, rotation_w, gravity_x, gravity_y, gravity_z = struct.unpack('<hhhhhhh',
                                                                                                        data[:14])
        rotation = Rotation(
            x=rotation_x / 180.0 * 0.01,
            y=rotation_y / 180.0 * 0.01,
            z=rotation_z / 180.0 * 0.01 * -1.0,
            w=rotation_w / 180.0 * 0.01 * -1.0
        )

        # Check if there's enough data for gravity components
        if len(data) >= 20:
            gravity_x, gravity_y, gravity_z = struct.unpack('<hhh', data[14:20])
        else:
            gravity_x, gravity_y, gravity_z = 0.0, 0.0, 0.0

        gravity = Gravity(
            x=gravity_x / 256.0,
            y=gravity_y / 256.0,
            z=gravity_z / 256.0
        )
        return rotation, gravity
    except (struct.error, DecodeError) as e:
        raise DecodeError("Error decoding IMU packet") from e


if __name__ == "__main__":
    # Parse command argument(s), if any
    parser = argparse.ArgumentParser(description='Process the trackers from the GX6 Communication Dongle')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode and log output to a file.')
    args = parser.parse_args()

    # If --debug flag is provided, log to a file with the current date and time
    if args.debug:
        debug_mode = True
        logging.debug("Debug mode enabled, printing raw data and logging to file.")
        log_filename = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)

    start_server()
