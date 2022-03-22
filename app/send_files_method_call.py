import base64
import uuid
import math
import asyncio

from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod

# device settings - FILL IN YOUR VALUES HERE
IOTHUB_CONNECTION_STRING = "<YOUR_IOT_EDGE_GATEWAY_DEVICE_CONNECTION_STRING>"
device_id = "<YOUR_EDGE_DEVICE_ID>"
module_id = "receive_files"
method_name = "file"

# general purpose variables
registry_manager = None

# Send a file over the IoT Hub transport to IoT Central
async def send_file(method_name, filename, assetId):
    f = open(file=filename, mode="rb")
    data = f.read()
    file_size_kb = len(data) / 1024
    f.close()

    # encode the data with base64 for transmission as a JSON string
    data_base64 = base64.b64encode(data).decode("ASCII")

    # Maximum direct method payload size is 128 KB.
    max_msg_size = 125 * 1024
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

        payload = data_chunk
        if registry_manager:
            print("Start sending multi-part message")

            payload = {}
            payload["data"] = data_chunk
            payload["multipart-config-message"] = "yes";  # indicates this is a multi-part message that needs special processing
            payload["id"] = file_id;   # unique identity for the multi-part message we suggest using a UUID
            payload["assetId"] = assetId; # file path for the final file, the path will be appended to the base recievers path
            payload["part"] = str(part);   # part N to track ordring of the parts
            payload["maxPart"] = str(max_parts);   # maximum number of parts in the set
            
            try:
                deviceMethod = CloudToDeviceMethod(method_name=method_name, payload=payload)
                registry_manager.invoke_device_module_method(device_id=device_id, module_id=module_id, direct_method_request=deviceMethod)
                print("completed sending multi-part message")
            except Exception as err:
                status_message = "Received exception during method call"
                print(status_message)
                status = 500
            
        part = part + 1

    # send a file transfer status message to IoT Central over MQTT
    payload = {
        "filename": filename,
        "assetId": assetId,
        "status": {status},
        "message": {status_message},
        "size": {file_size_kb}
    }
    
    deviceMethod = CloudToDeviceMethod(method_name=method_name, payload=payload)
    registry_manager.invoke_device_module_method(device_id=device_id, module_id=module_id, direct_method_request=deviceMethod)
    print("completed sending file transfer status message")


async def main():
    global registry_manager
    print("Connecting to IoT Edge . . .")
    try:
        registry_manager = IoTHubRegistryManager(IOTHUB_CONNECTION_STRING)
    except Exception as e:
        print("Connection failed . . .")
        registry_manager = None

    if registry_manager != None:
        local_upload_dir = "./sample-upload-files/"

        # send an mp4 video file with compression
        await send_file(method_name, local_upload_dir + "video.mp4", "video.mp4")

        # send a pdf file with compression
        await send_file(method_name, local_upload_dir + "large-pdf.pdf", "large-pdf.pdf") # 10,386KB

        # send a jpg file without compression
        await send_file(method_name, local_upload_dir + "4k-image.jpg", "4k-image.jpg") # 3,914KB
    
    else:
        print('Cannot connect to Azure IoT Edge. Please check the connection string and machine connectivity . . .')


# start the main routine
if __name__ == "__main__":
    asyncio.run(main())