import subprocess
import requests
import xml.etree.ElementTree as ET
import os
import re
import lz4

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

def get_imei(device_id):
    """Retrieve the IMEI."""
    # Restart adb in root mode
    run_adb_command("adb root")

    # Execute the service call command
    command = f"adb -s {device_id} shell service call iphonesubinfo 1 s16 com.android.shell"
    output, error = run_adb_command(command)
    if error:
        print(f"Error retrieving IMEI: {error}")
        return None

    # Parse the output: extract digits from hex-encoded response
    imei = "".join(
        line.split("'")[-2]
        for line in output.splitlines()
        if "'" in line
    )
    imei = "".join(filter(str.isdigit, imei))
    
    if len(imei) != 15:  # IMEI should be 15 digits long
        print("Failed to parse IMEI correctly.")
        return None

    return imei

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

def download_firmware(csc, model, firmware_version, imei):
    """Download the firmware using SamFirm."""
    try:
        # Create the assets folder if it doesn't exist
        assets_dir = ".\\assets\\"
        firmware_dir = f".\\assets\\firmware\\{model}\\"
        os.makedirs(assets_dir, exist_ok=True)

        # Install samloader dynamically
        # print("Cloning SamFirm...")
        # os.makedirs(".\\assets\\samfirm\\", exist_ok=True)
        # subprocess.run(".\\get-samfirm-release.ps1", shell=True, check=True)

        # Download the firmware
        print(f"Downloading firmware for {model}, CSC {csc}, version {firmware_version}... (This may take a while)")    
        subprocess.run(
            f".\\assets\\samfirm\\SamFirm.exe -model {model} -region {csc} -imei {imei} -folder {firmware_dir} -autodecrypt -nozip",
            shell=True,
            check=True
        )
        print("Firmware download complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading firmware: {e}")



def find_most_recent_zip(folder_path):
    """Find the most recently modified or created ZIP file in the given folder.""" # dunno why i made an entire function for this but this will help with 
    zip_files = [f for f in os.listdir(folder_path) if f.endswith('.zip')]         # differenciating between two zips if there's ever a conflict 
    
    if not zip_files:
        print("No ZIP files found.")
        return None
    
    zip_files = [os.path.join(folder_path, f) for f in zip_files]
    
    most_recent_zip = max(zip_files, key=os.path.getmtime)
    
    return most_recent_zip

def extract_firmware(model):
    """Extract the firmware downloaded."""
    try:
        firmware_dir = f".\\assets\\firmware\\{model}\\"
        
        recent_zip = find_most_recent_zip(firmware_dir)
        if not recent_zip:
            print(f"No ZIP file found to extract for {model}.")
            return
        
        print(f"Extracting firmware for {model} from {recent_zip}... (This may take a while)")
        
        destination_dir = f".\\assets\\firmware\\{model}\\extracted\\"

        subprocess.call(f"powershell.exe Expand-Archive -Force {recent_zip} {destination_dir}", shell=True) # for some reason subprocess.run didn't wanna work
        print(f"Firmware extracted to {destination_dir}.")                                          # thankfully he's expendable. subprocess.call replaced him
        
        fw_device_model = model

        prefix_list = ["SM-", "GT-"]

        pattern = '|'.join(map(re.escape, prefix_list))
        fw_device_model = re.sub(r'\b(?:{})\b'.format(pattern), '', fw_device_model)

        # bl extraction time :blush: :crazy:11
        print(fw_device_model)

        for f in os.listdir(f".\\assets\\firmware\\{model}\\extracted\\"):
            if f.endswith('.tar.md5'):
                if f.startswith(f"BL_{fw_device_model}"):
                    print(F"Extracting {f}... (This may take a while)")
                    bl_filename = f

        os.makedirs(f".\\assets\\firmware\\{model}\\bl_extracted\\", exist_ok=True) # tar doesn't create directories on its own if it doesnt exist
        subprocess.call(f"powershell.exe tar -xf {destination_dir}{bl_filename} -C .\\assets\\firmware\\{model}\\bl_extracted\\", shell=True)
        print(f"Extracting param.bin.lz4... (this may take a while)")
        os.makedirs(f".\\assets\\firmware\\{model}\\param_extracted\\", exist_ok=True) 
        subprocess.call(f""" powershell.exe .\\assets\\lz4\\lz4.exe -d .\\assets\\firmware\\{model}\\bl_extracted\\param.bin.lz4 .\\assets\\firmware\\{model}\\param_extracted\\param.bin """, shell=True)
        print(f"Extracting param.bin... (this may take a while)")
        os.makedirs(f".\\assets\\firmware\\{model}\\param_extracted\\", exist_ok=True) 
        subprocess.call(f""" powershell.exe .\assets\7z-zstd\7z.exe e .\assets\firmware\SM-A205W\param_extracted\param.bin -o".\assets\firmware\SM-A205W\param-assets_extracted\" """, shell=True)
        subprocess.call(f""" powershell.exe .\assets\7z-zstd\7z.exe e .\assets\firmware\SM-A205W\param_extracted\param.bin -o".\assets\firmware\SM-A205W\param-assets_customizable\" """, shell=True)
        print(f"Finished. Extracted assets are at ./assets/firmware/{model}/param-assets_customizable/")
        print("IMPORTANT!")
        print("DO NOT MODIFY 'param-assets_extracted' unless you want to redownload your firmware!")
        print("'param-assets_extracted' is a backup and reference copy of the unmodified image assets.\.")
        print("They are used as both a backup and a reference for custom assets you make for your device.")
        # print(f"WARNING! Be very careful when modifying these images if you intend to edit them")
        # print(f"for your Samsung device. Making these assets bigger (as in image pixel size/scale, not storage size)")
        # print(f"could lead to unexpected consequences. This is your only warning, if you break,")
        # print(f"brick, fry, boil, initiate thermonuclear war with your device, it was YOUR fault.")

    except subprocess.CalledProcessError as e:
        print(f"Error extracting firmware: {e}")


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

    # Get IMEI
    imei = get_imei(selected_device)
    if not imei:
        print("Could not retrieve IMEI.")
        return
    print(f"IMEI: {imei}")

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
    download_firmware(csc_code, model, latest_build, imei)

    # extract said silly firmware
    extract_firmware(model)

if __name__ == "__main__":
    main()


