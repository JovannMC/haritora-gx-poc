# Hey welcome to the project, by JovannMC (and a bit too much of ChatGPT)
# I would recommend using a program like RealTerm to capture the serial data, and then "echo" the data to the server.

import socket
import struct

# Echo the data to these details for the program to interpret, recommended to use RealTerm.
HOST = '127.0.0.1'
PORT = 9876

# There's gotta be a better way to do this. Read below for more info.
prev_main_button_press_count = 0
prev_sub_button_press_count = 0

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
        print(f'Server listening on {HOST}:{PORT}')
        while True:
            client_socket, client_address = server_socket.accept()
            print(f'Connection established from {client_address}')
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
    # print(f"Processed lines: {lines}") - add --debug for this
    for line in lines:
        parts = line.split(b':', 1)
        if len(parts) == 2:
            label, data = parts
            if label == b'X0':
                # Tracker 1 data
                process_x0_data(data)
            elif label == b'X1':
                # Tracker 2 data
                process_x1_data(data)
            if label == b'a0':
                # Other tracker 1 data
                process_a0_data(data)
            elif label == b'a1':
                # Other tracker 2 data
                process_a1_data(data)
            if label == b'r0':
                # Button press data
                process_r0_data(data)
#
# Tracker data
# This is obviously the IMU tracking data, the juicy stuff. Can be used to forward to other software such as SlimeVR's server!
# Rotation has: x, y, z, w
# Gravity has: x, y, z
#

def process_x0_data(data):
    try:
        rotation, gravity = decode_imu_packet(data)
        print(f'X0 Rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w}')
        print(f'X0 Gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
    except DecodeError as e:
        print("Error decoding X0 IMU packet:", e)

def process_x1_data(data):
    try:
        rotation, gravity = decode_imu_packet(data)
        print(f'X1 Rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w}')
        print(f'X1 Gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
    except DecodeError as e:
        print("Error decoding X1 IMU packet:", e)

#
# Other tracker data
# Currently unsure what other data a0/a1 could represent other than trying to finding the trackers, I see other values for it too.
# This could also be used to report calibration data when running the calibration thru the software.
#

def process_a0_data(data):
    decoded_data = data.decode('utf-8')
    if decoded_data.strip() == '7f7f7f7f7f7f':
        print("Searching for tracker 0...")
    else:
        print(f"Processing A0 data: {decoded_data}")

def process_a1_data(data):
    decoded_data = data.decode('utf-8')
    if decoded_data.strip() == '7f7f7f7f7f7f':
        print("Searching for tracker 1...")
    else:
        print(f"Processing A0 data: {decoded_data}")

#
# Tracker button data
# Here we're processing the button pressed, the 7th/10th character in the decoded data is the amount of times the main/sub buttons were pressed respectively.
#

def process_r0_data(data):   
    decoded_data = data.decode('utf-8')

    global prev_main_button_press_count, prev_sub_button_press_count
    main_button_press_count = int(decoded_data[6], 16)  # 7th character (0-indexed)
    sub_button_press_count = int(decoded_data[9], 16)  # 10th character (0-indexed)

    # This is a pretty janky way to track which button has been pressed, but seems to be the best way right now.
    # This is due to how the data is received (r1:110060800400), where both the main button (8) and sub button (4) are tracked in the same 12 bits.
    if main_button_press_count != prev_main_button_press_count:
        print(f"Main button pressed. Pressed {main_button_press_count + 1} times.")
        prev_main_button_press_count = main_button_press_count
    elif sub_button_press_count != prev_sub_button_press_count:
        print(f"Sub button pressed. Pressed {sub_button_press_count + 1} times.")
        prev_sub_button_press_count = sub_button_press_count
    else:
        print("No new button press detected.. wait how did this run?")
        print(decoded_data)

#
# Decoding IMU packets
# The logic to decode the IMU packet received by the dongle. Thanks to sim1222's project for helping with the math :p
# https://github.com/sim1222/haritorax-slimevr-bridge/
#

def decode_imu_packet(data):
    try:
        if len(data) < 20:
            raise DecodeError("Too few bytes to decode IMU packet")

        rotation_x, rotation_y, rotation_z, rotation_w, gravity_x, gravity_y, gravity_z = struct.unpack('<hhhhhhh', data[:14])
        rotation = Rotation(
            x=rotation_x / 180.0 * 0.01,
            y=rotation_y / 180.0 * 0.01,
            z=rotation_z / 180.0 * 0.01 * -1.0,
            w=rotation_w / 180.0 * 0.01 * -1.0
        )
        gravity = Gravity(
            x=gravity_x / 256.0,
            y=gravity_y / 256.0,
            z=gravity_z / 256.0
        )
        return rotation, gravity
    except (struct.error, DecodeError) as e:
        raise DecodeError("Error decoding IMU packet") from e

if __name__ == "__main__":
    start_server()
