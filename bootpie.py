import subprocess
import requests
import xml.etree.ElementTree as ET
import os

def run_adb_command(command):
    """Run an ADB command and return the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            return None, result.stderr.strip()
        return result.stdout.strip(), None
    except Exception as e:
        return None, str(e)

def list_connected_devices():
    """List all devices connected via ADB."""
    output, error = run_adb_command("adb devices")
    if error:
        print(f"Error: {error}")
        return []

    devices = []
    lines = output.splitlines()
    for line in lines[1:]:  # Skip the header line
        parts = line.split()
        if len(parts) > 1 and parts[1] == "device":
            devices.append(parts[0])

    return devices

def get_csc_code(device_id):
    """Retrieve the CSC code by reading /efs/imei/omcnw_code.dat."""
    run_adb_command(f"adb root")
    output, error = run_adb_command(f"adb -s {device_id} shell cat /efs/imei/omcnw_code.dat")
    if error:
        print(f"Error retrieving CSC code: {error}")
        return None
    return output.strip()

def fetch_latest_firmware(csc, model):
    """Fetch the latest firmware version from the XML endpoint."""
    url = f"https://minimal-proxy.glitch.me/proxy?url=https://fota-cloud-dn.ospserver.net/firmware/{csc}/{model}/version.xml"
    print(f"Fetching firmware information from: {url}")
    

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse the XML response
        root = ET.fromstring(response.content)

        # Extract the latest firmware version
        latest_element = root.find("./firmware/version/latest")
        if latest_element is not None:
            latest_version = latest_element.text.split("/")[0]  # Get the first entry of the latest firmware string
            return latest_version

    except Exception as e:
        print(f"Error fetching firmware information: {e}")
        return None

def download_firmware(csc, model, firmware_version):
    """Download the firmware using SamFirm."""
    try:
        # Create the assets folder if it doesn't exist
        assets_dir = "./assets/"
        os.makedirs(assets_dir, exist_ok=True)
        
        # Install samloader dynamically
        print("Cloning SamFirm...")
        os.makedirs("./assets/samfirm/", exist_ok=True)
        subprocess.run("./get-samfirm-release.ps1", shell=True, check=True)

        # Download the firmware
        print(f"Downloading firmware for {model}, CSC {csc}, version {firmware_version}...")
        subprocess.run(
            f"samloader download -m {model} -r {csc} -v {firmware_version} -o {assets_dir}",
            shell=True,
            check=True
        )
        print("Firmware download complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading firmware: {e}")

def main():
    # List connected devices
    devices = list_connected_devices()
    if not devices:
        print("No devices found. Make sure USB debugging is enabled and devices are connected.")
        return

    print("Connected devices:")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device}")

    # Select a device
    try:
        choice = int(input("Select a device (number): ")) - 1
        if choice < 0 or choice >= len(devices):
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    selected_device = devices[choice]
    print(f"Selected device: {selected_device}")

    # Get CSC code
    csc_code = get_csc_code(selected_device)
    if not csc_code:
        print("Could not retrieve CSC code.")
        return
    print(f"CSC Code: {csc_code}")

    # Get device model
    model, error = run_adb_command(f"adb -s {selected_device} shell getprop ro.product.model")
    if error or not model:
        print(f"Error retrieving model: {error}")
        return
    model = model.strip()
    print(f"Device Model: {model}")

    # Fetch the latest firmware version
    print("Searching for the latest firmware version...")
    latest_build = fetch_latest_firmware(csc_code, model)
    if not latest_build:
        print("Could not retrieve the latest firmware version.")
        return
    print(f"Latest Firmware Build: {latest_build}")

    # Download firmware
    download_firmware(csc_code, model, latest_build)

if __name__ == "__main__":
    main()


