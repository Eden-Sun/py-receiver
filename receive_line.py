from os import environ
import serial
import requests
import threading
import time

# Replace with your actual serial port and baud rate
SERIAL_PORT = "/dev/ttyUSBLOCK"
BAUD_RATE = 9600


# Replace with your Mackerel API key
API_KEY = environ.get("KEY")

# Mackerel API endpoint
API_ENDPOINT = "https://api.mackerelio.com/api/v0/services/Voltage/tsdb"

print(API_KEY)
exit(1) if API_KEY is None else print("API_KEY is set")

# Create a serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

# Event to signal the space thread to reset
reset_space_thread_event = threading.Event()


def send_space_to_serial():
    while True:
        try:
            if reset_space_thread_event.wait(
                5 if reset_space_thread_event.is_set() else 10
            ):
                reset_space_thread_event.clear()

            # Send a space character to the serial port
            ser.write(b" ")

            # Print log message with timestamp (time only)
            current_time = time.strftime("%H:%M:%S")
            print(f"Sent at {current_time}: Space character")

        except Exception as e:
            print(f"Error sending space character: {e}")
            time.sleep(10)


# Create and start the space-sending thread
space_thread = threading.Thread(target=send_space_to_serial)
# This thread will automatically exit when the main program exits
space_thread.daemon = True
space_thread.start()


def getPercent(voltage):
    p = 0
    if voltage > 11.36:
        p = (voltage - 11.36) * 0.015
    if voltage > 11.96:
        p = 40 + (voltage - 11.96) * 0.014
    if voltage > 12.24:
        p = 60 + (voltage - 12.24) * 0.013
    if voltage > 12.5:
        p = 80 + (voltage - 12.5) * 0.012
    if voltage > 12.62:
        p = 90 + (voltage - 12.62) * 0.012
    return int(p)


try:
    while True:
        try:
            # Read data from the serial port
            data = ser.readline().decode("utf-8").strip()
            voltage = int(data) * 0.02269
            voltage = round(voltage, 2)
            percent = getPercent(voltage)

            # Print received data with timestamp (time only)
            current_time = time.strftime("%H:%M:%S")
            print(f"Received at {current_time}: {data} {percent}%")

            # Set the reset event to reset the space thread
            reset_space_thread_event.set()

            access_token = API_KEY

            # URL for the Line Notify API
            url = 'https://notify-api.line.me/api/notify'

            # Message to send
            message = f"Got value: {data} {voltage}"

            # Set headers with the access token
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            # Data to send in the POST request
            data = {
                'message': message
            }

            # Send the POST request to Line Notify
            response = requests.post(url, headers=headers, data=data)

            # Print API response
            print(f"API Response: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error processing serial data: {e}")
            print("sleep and reopen")
            ser.close()
            time.sleep(10)
            ser.open()

except KeyboardInterrupt:
    # Close the serial connection on Ctrl+C
    ser.close()
    print("Serial connection closed.")
