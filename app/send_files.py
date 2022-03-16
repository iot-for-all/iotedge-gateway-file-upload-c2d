import base64
import uuid
import math
import asyncio

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

# device settings - FILL IN YOUR VALUES HERE
ROOT_CA_CERT_FILE = "<YOUR_ROOT_CA_CERT_FILE_PATH>"
GATEWAY_HOST_NAME = "<YOUR_VM_PUBLIC_IP_ADDRESS>"
DEVICE_CONNECTION_STRING = "<YOUR_IOT_EDGE_GATEWAY_DEVICE_CONNECTION_STRING>"

# general purpose variables
use_websockets = False
device_client = None

# Send a file over the IoT Hub transport to IoT Central
async def send_file(filename, assetId):
    f = open(file=filename, mode="rb")
    data = f.read()
    file_size_kb = len(data) / 1024
    f.close()

    # encode the data with base64 for transmission as a JSON string
    data_base64 = base64.b64encode(data).decode("ASCII")

    max_msg_size = 255 * 1024
    max_content_size = max_msg_size
    
    max_parts = int(math.ceil(len(data_base64) / max_content_size))
    file_id = uuid.uuid4()
    part = 1
    index = 0

    # chunk the file payload into 255KB chunks to send to IoT central over MQTT (could also be AMQP or HTTPS)
    status = 200
    status_message = "completed"
    for i in range(max_parts):
        data_chunk = data_base64[index:index + max_content_size]
        index = index + max_content_size
        
        # payload = multipart_msg_schema.format(data_chunk)
        payload = data_chunk
        if device_client and device_client.connected:
            print("Start sending multi-part message")

            msg = Message(payload)
            
            # standard message properties
            msg.content_type = "application/json";  # when we support binary payload this should be changed to application/octet-stream
            msg.content_encoding = "utf-8"; # encoding for the payload utf-8 for JSON and can be left off for binary data

            # custom message properties
            msg.custom_properties["multipart-message"] = "yes";  # indicates this is a multi-part message that needs special processing
            msg.custom_properties["id"] = file_id;   # unique identity for the multi-part message we suggest using a UUID
            msg.custom_properties["assetId"] = assetId; # file path for the final file, the path will be appended to the base recievers path
            msg.custom_properties["part"] = str(part);   # part N to track ordring of the parts
            msg.custom_properties["maxPart"] = str(max_parts);   # maximum number of parts in the set
            
            try:
                await device_client.send_message(msg)
                print("completed sending multi-part message")
            except Exception as err:
                status_message = "Received exception during send_message. Exception: " + err
                print(status_message)
                status = 500
            
        part = part + 1

    # send a file transfer status message to IoT Central over MQTT
    payload = f'{{"filename": "{filename}", "assetId": "{assetId}", "status": {status}, "message": "{status_message}", "size": {file_size_kb}}}'
    msg = Message(payload)
            
    # standard message properties
    msg.content_type = "application/json";  # when we support binary payload this should be changed to application/octet-stream
    msg.content_encoding = "utf-8"; # encoding for the payload utf-8 for JSON and can be left off for binary data

    await device_client.send_message(msg)
    print("completed sending file transfer status message")


async def main():
    global device_client
    print("Connecting to IoT Edge module . . .")
    try:
        certfile = open(ROOT_CA_CERT_FILE)
        root_ca_cert = certfile.read()
        connStr = "{};GatewayHostName={}".format(DEVICE_CONNECTION_STRING, GATEWAY_HOST_NAME)
        device_client = IoTHubDeviceClient.create_from_connection_string(connection_string=connStr, server_verification_cert=root_ca_cert, websockets=use_websockets)
        await device_client.connect()
    except Exception as e:
        print("Connection failed . . .")
        device_client = None

    if device_client != None:
        local_upload_dir = "./sample-upload-files/"

        # send an mp4 video file with compression
        await send_file(local_upload_dir + "video.mp4", "video.mp4")

        # send a pdf file with compression
        await send_file(local_upload_dir + "large-pdf.pdf", "large-pdf.pdf") # 10,386KB

        # send a jpg file without compression
        await send_file(local_upload_dir + "4k-image.jpg", "4k-image.jpg") # 3,914KB

        # disconnect from IoT hub/central
        print("Disconnecting from IoT Edge Module")
        await device_client.disconnect()
    else:
        print('Cannot connect to Azure IoT Edge module. Please check the connection string and machine connectivity . . .')


# start the main routine
if __name__ == "__main__":
    asyncio.run(main())