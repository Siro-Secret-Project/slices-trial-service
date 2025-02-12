import time
import os
import random
import struct
import binascii


def generate_object_id():
    # Get current timestamp (first 4 bytes)
    timestamp = struct.pack(">I", int(time.time()))

    # Generate 5 random bytes (machine ID + process ID)
    machine_pid = os.urandom(5)

    # Generate 3 random bytes (counter)
    counter = struct.pack(">I", random.getrandbits(24))[1:]

    # Combine all parts
    object_id = timestamp + machine_pid + counter

    # Convert to hex string
    return binascii.hexlify(object_id).decode()