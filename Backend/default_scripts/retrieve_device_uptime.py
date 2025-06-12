import subprocess
import re

def retrieve_device_uptime():
    # Call the dmcli command to retrieve the device uptime
    result = subprocess.run(["dmcli", "eRT", "getv", "Device.DeviceInfo.UpTime"], capture_output=True, text=True)
    
    # Check if the output satisfies the expected result
    if re.search(r'\d+(\.\d+)?', result.stdout):
        print(result.stdout.strip())
        print("[PASS]")
    else:
        print("[FAIL]")

if __name__ == "__main__":
    retrieve_device_uptime()
