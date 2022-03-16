# iotc-file-upload
# Uploading large payloads to IoT Edge Gateway device using the Azure IoT device SDK and a single connection

## Description

Uploading large payloads to IoT Edge Gateway device, it has typically been achieved by using blob storage in the midst. This works by configuring an Azure BLOB Storage container and sharing container key with IoT Edge Gateway and cloud app for writting and reading blobs. Using container allows the device to open an HTTPS connection to the BLOB storage container for downloading the large payload.  Whilst this is an effective and secure way to push large payloads it does require the device to open a second secure connection to the Azure cloud something that can be a challenge for constrained devices. Not to mention, managing and sharing container's security with cloud and device requires additional maintence headache.

This sample shows how you can push large payloads up to IoT Edge Gateway device from cloud using the standard IoT transports (MQTT, AMQP, HTTPS) and without the need to open a second connection.

## How it works

### From cloud side
Using device SDK, connect to IoT Edge Gateway just like a child device would send regular telemetry to IoT Edge Gateway
This can be via the standard transports of MQTT, AMQP, or HTTPS. Once connected, cloud can send telemetry and properties as normal.  When a large payload needs to be transmitted to IoT Edge Gateway it is chunked into smaller payloads of 255KB and custom message properties are applied to the payloads indicating the file properties.

The custom message properties are as follows (all properties are required):

|Custom Property|Value example|Description|
|---------------|-------------|-----------|
|multipart-message|yes|signifies a large payload that is multi-part and should always have a value of yes|
|id|96a67e1d-662c-43fb-9440-ddcb29d9b817|a UUID4 identifier for the set of parts in this upload|
|assetId|pic.jpg|the file name for the file when saved in the IoT Edge|
|part|1|the part number of the chunk
|maxPart|5|the maximum number of chunks in the upload

Standard message properties are as follows:

|Standard Property|Value example|Description|
|---------------|-------------|-----------|
|content_type|application/json|describes the content type of the payload.  For now only application/json is supported.  Later releases might see binary format supported with content type application/octet-stream|
|content_encoding|utf-8|describes the encoding schema for the payload data.  For now only utf-8 is supported.  Later releases might see binary format supported in that case this property is not required|

Because the payload might contain binary data the payload should be converted to a base64 string. The processing flow is as follows:

<ol>
<li> Base64 convert the data </li>
<li> Chunk the data from step 1 into 255KB parts </li>
<li> Form an Azure IoT message payload from each chunk and apply the necessary standard and custom properties appropriatly </li>
<li> Send the message to Azure IoT Edge </li>
<li> Repeat steps 3 and 4 until all the chunks have been sent </li>
</ol>

Once the final chunk has been sent you can optionally send a confirmation message to IoT Edge indicating that a large payload has been sent

|Custom Property|Description|
|---------------|-------------|
|filename|description of what was sent, either a file name or payload description|
|assetId|file name supposed to be created in IoT Edge|
|status|a status code indicating sucess or failure (uses standard HTTP status codes)|
|message|a custom status message describing the success or error|
|size|the size of the payload data sent (prior to compression or base64 encoding)|

An example of the payload would look like this:

```
    {
        "filename": "./sample-upload-files/4k-image.jpg",
        "assetId": "4k-image.jpg",
        "status": 200,
        "message": "completed",
        "size": 3913.5166015625
    }
```

### From the IoT Edge Gateway side

IoT Edge Gateway routes the messages received to a custom module for further processing.
Receiving IoT Edge module filters on the message property 'multipart-message' equals 'yes' and re-construct the payload form the received data chunks.

IoT Edge Gateway module should process the files at a minimum as follows for each incoming payload chunk:

<ol>
<li> Cache the payload chunk in memory with a key of the custom message property 'id' value and an extension of the custom message property 'part' value.</li>
<li> Count the number of entries cached to see if they match the number in the custom message property 'maxPart'.  If they do then process the set as shown in the next section.</li>
</ol>

Once all the parts have been received the following processing should be done:

<ol>
<li> Concatenate the file parts together in the order of the extension 1 thru N </li>
<li> Take the concatenated file and base64 decode the contents. </li>
<li> Save the contents of step 2 to a file using the custom message property 'assetId' value as file name. </li>
</ol>

## Using this sample
1. install required tools:
    - Install [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
    - Install [Putty and PSCP](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)
2. Build and publish [custom IoT Edge module](https://github.com/iot-for-all/iotedge-gateway-file-upload-c2d/tree/main/edge-gateway-modules/receive-files/README.md)
2. Create free or standard IoT hub using [Azure portal](https://ms.portal.azure.com/)
3. In the [Azure portal](https://ms.portal.azure.com/), navigate to your IoT hub
4. Select IoT Edge from the navigation menu
5. Select Add an IoT Edge device
6. Click on created IoT Edge device then click on "Set modules" tab
7. On Set modules on device page +Add IoT Edge Module you created in step #2
8. Click on "Container Create Option" and paste in the following json
    ```json
    {
        "HostConfig": {
            "Mounts":[
                {
                    "Type":"bind",
                    "Source": "/etc/files",
                    "Target": "/files",
                    "RW": true,
                    "Propagation":"rprivate"
                }
            ]
        }
    }
    ```
9. Click on Routes tab and add the following routes:
    ```json
    "routes": {
        "hub_to_crud": "FROM /* WHERE NOT IS_DEFINED($connectionModuleId) INTO BrokeredEndpoint(\"/modules/receive_files/inputs/input1\")",
        "crud_to_hub": "FROM /* WHERE IS_DEFINED($connectionModuleId) INTO $upstream"
    }
    ```
10. Click on Review + Create then Create. 
11. Note the IoT Edge device connection string
12. [Create and provision a single Linux IoT Edge device](edgevm.md)
13. [Build and execute script](https://github.com/iot-for-all/iotedge-gateway-file-upload-c2d/tree/main/app/README.md) to send the files
14. SSH in to IoT Edge Gateway device (using Putty) and verify the files are created in /etc/files folder:
    ```Linux
    ls /etc/files
    ```

