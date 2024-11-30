import requests
import xml.etree.ElementTree as ET


test_csc = "XAC"
test_model = "SM-A205W"
url = f"https://minimal-proxy.glitch.me/proxy?url=https://fota-cloud-dn.ospserver.net/firmware/{test_csc}/{test_model}/version.xml"
response = requests.get(url)
print(response.status_code)
print(response.text)

