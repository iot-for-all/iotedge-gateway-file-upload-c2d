# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
import base64
import sys
sys.path.insert(0, "..")
import asyncio
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse

module_client = None
startTimer = time.process_time()

config_chunks = {}
async def file_processor(payload):
    multi_part = payload.get("multipart-config-message")
    data = payload.get("data")
    print("file_processor: multi_part: {}".format(multi_part))
    # print("file_processor: data: \n{}".format(data))
    if data and multi_part and multi_part == "yes":
        id = payload.get("id")
        print("multi part message received: {}".format(id))
        config = config_chunks.get(id)
        if config == None:
            print("setting config_chunks: {}".format(id))
            config_chunks[id] = {}
            config_chunks[id].update({"assetId": payload.get("assetId")})
            config_chunks[id].update({"maxPath": payload.get("maxPart")})
            config_chunks[id].update({"parts": {}})
        
        config = config_chunks.get(id)
        print("Processing part: {}".format(payload.get("part")))
        parts = config.get("parts")
        parts.update({payload.get("part"): data})
        
        # check to see if all the file parts are available
        if len(parts) == int(config.get("maxPath")):
            print("Recieved all parts: {}".format(config.get("maxPath")))
            encodedData = ""
            for key, value in parts.items():
                print("- Processing chunk: {}".format(key))
                encodedData = encodedData + value
            
            decodedData = base64.b64decode(encodedData)
            
            # write to disk
            fileName = config.get("assetId")
            print("Creating config file: {}".format(fileName))
            file = open("/files/{}".format(fileName), "wb")
            file.write(decodedData)
            file.close()
            print("Cleaning up cached chunks . . .")
            config_chunks.pop(id)
            # print(decodedData)


async def method_request_handler(method_request):
    try:
        method_name = method_request.name
        payload = method_request.payload
        
        multi_part = payload.get("multipart-message")
        id = payload.get("id")
        assetId = payload.get("assetId")
        part = payload.get("part")
        maxPart = payload.get("maxPart")
        status = payload.get("status")
        
        print ("Method called with: name = {}\n\tmultipart-message: {}\n\tid: {}\n\tassetId: {}\n\tpart: {}\n\tmaxPart: {}".format(method_name, multi_part, id, assetId, part, maxPart))
        if method_name == "file":
            await file_processor(payload)
            payload = {"result": True, "data": "successfully processed"}  # set response payload
            status = 200  # set return status code
            print("executed method file")
        else:
            payload = {"result": False, "data": "unknown method"}  # set response payload
            status = 400  # set return status code
            print("executed unknown method: " + method_request.name)
                
        # Send the response
        method_response = MethodResponse.create_from_method_request(method_request, status, payload)
        await module_client.send_method_response(method_response)
        print('Method executed!')

    except Exception as e:
        print("method_request_handler: Processing Method Call failed with exception: {}".format(e))
        pass


async def message_handler(message):
    print("Message received on INPUT 1")
    print("custom properties: {}".format(message.custom_properties))
    if message == None or message.custom_properties == None:
        return
    
    multi_part = message.custom_properties.get('multipart-config-message')
    if multi_part and multi_part == "yes":
        id = message.custom_properties.get('id')
        print("multi part message received: {}".format(id))
        config = config_chunks.get(id)
        if config == None:
            print("setting config_chunks: {}".format(id))
            config_chunks[id] = {}
            config_chunks[id].update({"assetId": message.custom_properties.get('assetId')})
            config_chunks[id].update({"maxPath": message.custom_properties.get('maxPart')})
            config_chunks[id].update({"parts": {}})
        
        config = config_chunks.get(id)
        print("Processing part: {}".format(message.custom_properties.get('part')))
        parts = config.get("parts")
        parts.update({message.custom_properties.get('part'): message.data})
        
        # check to see if all the file parts are available
        if len(parts) == int(config.get("maxPath")):
            print("Recieved all parts: {}".format(config.get("maxPath")))
            encodedData = "".encode("ASCII")
            for key, value in parts.items():
                print("- Processing chunk: {}".format(key))
                encodedData = encodedData + value
            
            decodedData = base64.b64decode(encodedData)
            
            # write to disk
            fileName = config.get("assetId")
            print("Creating config file: {}".format(fileName))
            file = open("/files/{}".format(fileName), "wb")
            file.write(decodedData)
            file.close()
            print("Cleaning up cached chunks . . .")
            config_chunks.pop(id)
            # print(decodedData)


async def internal_processor():
    global startTimer
    startTimer = time.process_time()
    while True:
        try:
            if time.process_time() - startTimer > 10:
                startTimer = time.process_time()
                print("hartbeat . . .")
                
        except Exception as e:
            print("incoming_queue_processor: Processing incoming queue failed with exception: {}".format(e))
            pass


async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IotEdge module Client for Processing messages" )

        # The client object is used to interact with your Azure IoT hub.
        global module_client
        global startTimer
        
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()
                
        # set the message handler on the module
        module_client.on_message_received = message_handler
        
        module_client.on_method_request_received = method_request_handler
       
        tasks = []
        tasks.append(asyncio.create_task(internal_processor()))
        await asyncio.gather(*tasks)

        print ( "Disconnecting . . .")

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error {}".format(e))
        raise
        
if __name__ == "__main__":
    asyncio.run(main())