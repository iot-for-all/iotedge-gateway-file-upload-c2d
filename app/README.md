# Send files script

## Prerequisite:
- Install Python 3.7 or higher from [here](https://www.python.org/downloads/)
- Install pip from [here](https://www.makeuseof.com/tag/install-pip-for-python/)

## Build and publish OPC UA crud module
1. Copy the [provided folder](https://github.com/iot-for-all/iotedge-gateway-file-upload-c2d/tree/main/app) to your development machine and open it in VSCode
2. Install necessary packages by executing the following commans:
    ```python
    pip install -r requirements.txt
    ```
3. Open the send_files.py file in vscode and change lines 10 - 12 adding in the path to your root ca cert, your IoT Edge Gateway hostName, and the IoT Edge Gateway device connection string:
    ```python
    # device settings - FILL IN YOUR VALUES HERE
    ROOT_CA_CERT_FILE = "<YOUR_ROOT_CA_CERT_FILE_PATH>"
    GATEWAY_HOST_NAME = "<YOUR_VM_PUBLIC_IP_ADDRESS>"
    DEVICE_CONNECTION_STRING = "<YOUR_IOT_EDGE_GATEWAY_DEVICE_CONNECTION_STRING>"
    ```
4. The code can then be run either from within Visual Studio Code or the command line with:
    ```
    python send_files.py
    ```

Running the above code will push three large payloads to the IoT Edge Gateway device.

|File|Size|Compressed|Description|
|----|----|----------|-----------|
|4k-image.jpg|3,914KB|no|a large jpeg image|
|large-pdf.pdf|10,386KB|yes|a large pdf file with images in it|
|video.mp4|10,300KB|yes|an mp4 encoded video file with sound|
