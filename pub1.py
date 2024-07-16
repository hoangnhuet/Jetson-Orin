import serial
import struct
import time
from pynput import keyboard

# Initial and target velocities
linear_velocity = 0.0
angular_velocity = 0.0
target_linear_velocity = 0.0
target_angular_velocity = 0.0

# Velocity increment for smoothing
velocity_increment = 0.01

def constrain(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def create_message(linear_velocity, angular_velocity):
    # Constrain the velocities to their limits
    linear_velocity = constrain(linear_velocity, 0, 0.5)
    angular_velocity = constrain(angular_velocity, 0, 1.0)
    
    linear_velocity_scaled = int(linear_velocity * 10000)
    angular_velocity_scaled = int(angular_velocity * 10000)
    
    # Pack the values into the message
    message = bytearray(8)
    message[0] = 0x03
    message[1:3] = struct.pack('>H', linear_velocity_scaled)  # 2 bytes for linear velocity
    message[3:5] = struct.pack('>H', angular_velocity_scaled)  # 2 bytes for angular velocity
    # The remaining bytes are 0 except the checksum
    message[7] = sum(message[:-1]) % 256  # Calculate checksum
    
    return message

def send_message(port='/dev/ttyUSB0', baudrate=2000000, timeout=1):
    try:
        # Establish serial connection
        ser = serial.Serial(port, baudrate, timeout=timeout, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS)
        
        if ser.is_open:
            print(f"Serial connection established on {port} with baudrate {baudrate}")
            message = create_message(linear_velocity, angular_velocity)
            ser.write(message)
            print(f"Sent message: {message.hex()}")
        
        ser.close()
        print("Serial connection closed")
        
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")

def on_press(key):
    global target_linear_velocity, target_angular_velocity
    try:
        if key.char == 'w':
            target_linear_velocity += 0.1
        elif key.char == 'x':
            target_linear_velocity -= 0.1
        elif key.char == 'a':
            target_angular_velocity += 0.1
        elif key.char == 'd':
            target_angular_velocity -= 0.1
        elif key.char == 's':
            target_linear_velocity = 0.0
            target_angular_velocity = 0.0
        
        # Constrain target velocities within their limits
        target_linear_velocity = constrain(target_linear_velocity, 0, 0.5)
        target_angular_velocity = constrain(target_angular_velocity, 0, 1.0)
        
        # Print target velocities
        print(f"Target Linear Velocity: {target_linear_velocity}, Target Angular Velocity: {target_angular_velocity}")
        
    except AttributeError:
        pass

def adjust_velocity():
    global linear_velocity, angular_velocity
    if linear_velocity < target_linear_velocity:
        linear_velocity = min(linear_velocity + velocity_increment, target_linear_velocity)
    elif linear_velocity > target_linear_velocity:
        linear_velocity = max(linear_velocity - velocity_increment, target_linear_velocity)

    if angular_velocity < target_angular_velocity:
        angular_velocity = min(angular_velocity + velocity_increment, target_angular_velocity)
    elif angular_velocity > target_angular_velocity:
        angular_velocity = max(angular_velocity - velocity_increment, target_angular_velocity)

if __name__ == "__main__":
    # Setup the listener for keyboard inputs
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    try:
        while True:
            time.sleep(0.1) 
            adjust_velocity()
            send_message()
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        listener.stop()
