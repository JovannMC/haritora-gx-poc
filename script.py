import socket
from quaternion import quaternion
import struct

HOST = '127.0.0.1'  # Localhost
PORT = 9876         # Choose any available port

class DecodeError(Exception):
    pass

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
            process_data(data.decode('utf-8'))

def process_data(data):
    lines = data.strip().split('\n')
    for line in lines:
        parts = line.split(':', 1)
        if len(parts) == 2:
            label, data = parts
            if label == 'X1':
                process_x1_data(data)

def process_x1_data(data):
    # Decode IMU packet using Rust logic
    rotation, gravity = decode_imu_packet(data)
    print(f'Rotation: {rotation}, Gravity: {gravity}')

# Define the Rust function's logic in Python
def decode_imu_packet(data):
    try:
        # Unpack the data according to the format used in the Rust function
        rotation_x, rotation_y, rotation_z, rotation_w, gravity_x, gravity_y, gravity_z = struct.unpack('<hhhhhhh', data)

        # Scale the rotation values
        rotation_x = rotation_x / 180.0 * 0.01
        rotation_y = rotation_y / 180.0 * 0.01
        rotation_z = rotation_z / 180.0 * 0.01 * -1.0
        rotation_w = rotation_w / 180.0 * 0.01 * -1.0

        # Scale the gravity values
        gravity_x = gravity_x / 256.0
        gravity_y = gravity_y / 256.0
        gravity_z = gravity_z / 256.0

        # Return the decoded rotation and gravity data
        return (rotation_x, rotation_y, rotation_z, rotation_w), (gravity_x, gravity_y, gravity_z)
    except struct.error:
        # Handle the case where there's insufficient data to unpack
        raise DecodeError("Too few bytes to decode IMU packet")

def decode_imu_packet(data):
    try:
        if len(data) < 14:
            raise DecodeError("Too few bytes to decode IMU packet")
            
        rotation_x, rotation_y, rotation_z, rotation_w, gravity_x, gravity_y, gravity_z = struct.unpack('<hhhhhhh', data[:14])
        return rotation_x, rotation_y, rotation_z, rotation_w, gravity_x, gravity_y, gravity_z
    except (struct.error, DecodeError) as e:
        raise DecodeError("Error decoding IMU packet") from e

if __name__ == "__main__":
    # Example usage of decode_imu_packet function
    data = b'\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00\x07'  # Example data
    try:
        rotation_values = decode_imu_packet(data)
        print("Rotation values:", rotation_values)
    except DecodeError as e:
        print("Error decoding IMU packet:", e)
