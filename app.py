import requests

PI_ADDRESS = "http://raspberrypi.local:5000/capture"   # Using Pi's IP address

response = requests.post(PI_ADDRESS)

if response.status_code == 200:
    with open("test.jpg", "wb") as file:
        file.write(response.content)

    print("Image received")
else:
    print("Failed:", response.status_code)