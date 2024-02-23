import socket
import struct

HOST = '127.0.0.1'
PORT = 9876

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
    lines = data.strip().split(b'\n')  # Use bytes separator
    print(f"Processed lines: {lines}")
    for line in lines:
        parts = line.split(b':', 1)  # Use bytes separator
        if len(parts) == 2:
            label, data = parts
            if label == b'X0':
                process_x0_data(data)
            elif label == b'X1':
                process_x1_data(data)
            #elif label == b'a0':
                process_a0_data(data)
            #elif label == b'a1':
                process_a1_data(data)

def process_x0_data(data):
    try:
        # Decode IMU packet
        rotation, gravity = decode_imu_packet(data)
        print(f'Processing X0 IMU data - Rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w}), Gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
    except DecodeError as e:
        print("Error decoding X0 IMU packet:", e)

def process_x1_data(data):
    try:
        # Decode IMU packet
        rotation, gravity = decode_imu_packet(data)
        print(f'Processing X1 IMU data - Rotation: ({rotation.x}, {rotation.y}, {rotation.z}, {rotation.w}), Gravity: ({gravity.x}, {gravity.y}, {gravity.z})')
    except DecodeError as e:
        print("Error decoding X1 IMU packet:", e)

def process_a0_data(data):
    # To add specific print statements (looking for device, detecting if user activated calibration, etc.
    print(f"Processing A0 data: {data.decode('utf-8')}")

def process_a1_data(data):
    # To add specific print statements (looking for device, detecting if user activated calibration, etc.
    print(f"Processing A1 data: {data.decode('utf-8')}")

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
