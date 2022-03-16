# Deploy Azure IoT Edge Enabled Linux VM
Creating **Ubuntu Server LTS** based virtual machine will install the latest Azure IoT Edge runtime and its dependencies on startup, and makes it easy to connect to your IoT Central application via Device Provisioning Service (DPS)

## Requirements
- Install [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Install [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html)

## Create a virtual machine running Ubuntu LTS
1. Execute the following in Azure CLI
    ``` shell
    #!/bin/bash
    az login

    # Let az know which subscription should be used
    az account set --subscription <YOUR_SUBSCRIPTION_NAME>

    # Make sure resource group exists
    az group create \
        --name <YOUR_RESOURCE_GROUP_NAME> \
        --location <AZURE_REGION>

    # Create a new VM running Ubuntu LTS
    az vm create \
        --resource-group <YOUR_RESOURCE_GROUP_NAME> \
        --name <YOUR_VM_NAME> \
        --image UbuntuLTS \
        --admin-username <YOUR_USER_NAME> \
        --admin-password <YOUR_PASSWORD> \
        --size Standard_D2s_v3

    # Open port 22 for SSH
    az vm open-port \
        --port 22 \
        --resource-group <YOUR_RESOURCE_GROUP_NAME> \
        --name <YOUR_VM_NAME>
    ```
2. SSH to VM using [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/) and your VM ipAddress (get the ipAddress in portal.azure.com)
3. Install IoT Edge Gateway
    - 20.04:
        ```Linux
        wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
        sudo dpkg -i packages-microsoft-prod.deb
        rm packages-microsoft-prod.deb
        ```
    - 18.04:
        ```Linux
        wget https://packages.microsoft.com/config/ubuntu/18.04/multiarch/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
        sudo dpkg -i packages-microsoft-prod.deb
        rm packages-microsoft-prod.deb
        ```
    - Install a container engine
        ```Linux
        sudo apt-get update
        sudo apt-get install moby-engine
        ```
    - Install IoT Edge runtime
        ```Linux
        sudo apt-get update
        sudo apt-get install aziot-edge
        ```
    - Create config.toml from template
        ```Linux
        sudo cp /etc/aziot/config.toml.edge.template /etc/aziot/config.toml
        ```
4. Confirm Azure Edge Runtime is installed on the VM by executing the following command in SSH shell
    ```Linux
    iotedge version
    ```
5. Run the following command to create the **"certs"** folder for saving TLS certificates
    ```Linux
    sudo mkdir -p -v /etc/certs
    ```
6. Create TLS certificate and place them in /etc/certs folder using PSCP tool
    - Have the following files ready:
        - Root CA certificate
        - Device CA certificate
        - Device CA private key
    
        For production scenarios, you should generate those files with your own certificate authority.
        For development and test scenarios, you can use demo certificates.
        If you don't have your own certificate authority and want to use demo certificates, follow the instructions in
        [Create demo certificates to test IoT Edge device features](https://docs.microsoft.com/en-us/azure/iot-edge/how-to-create-test-certificates?view=iotedge-2020-11)
        to create your files. On that page, you need to take the following steps:

        1. To start, set up the scripts for generating certificates on your device.
        2. Create a root CA certificate. At the end of those instructions, you'll have a root CA certificate file:
            - <path>/certs/azure-iot-test-only.root.ca.cert.pem.
        3. Create IoT Edge device CA certificates. At the end of those instructions, you'll have a device CA certificate and its private key:
            - <path>/certs/iot-edge-device-ca-<cert name>-full-chain.cert.pem and
            - <path>/private/iot-edge-device-ca-<cert name>.key.pem

    - Copy above certificates to IoT Edge Gateway using the following PSCP command:
        ```
        pscp.exe -l <user> -pw <password> -P 22 -r <path>/<cert_folder> <user>@<YOUR_VM_IP_ADDRESS>:/etc 
        ```
    - Verify the certificates copied successfully, execute the following command in SSH window
        ```Linux
        ls /etc/certs
        ```
7. Run the following command to create the **"files"** folder for saving the large payloads
    ```Linux
    sudo mkdir -p -v /etc/files
    sudo chmod 777 /etc/files
    ```
8. Provision IoT Edge Gateway with its cloud identity
    ```Linux
    sudo nano /etc/aziot/config.toml
    ```
    - uncomment hostname = "<YOUR_VM_IP_ADDRESS>"
    - uncomment trust_bundle_cert = "file:///etc/certs/<YOUR_CERT>.root.ca.cert.pem"
    - under Manual provisioning with symmetric key:
        - uncomment [provisioning]
        - uncomment source = "manual"
        - uncomment connection_string = "<YOUR_REGISTERED_IOT_EDGE_CONNECTION_STRING>
    - under Edge CA certificates
        - uncomment [edge_ca]
        - uncomment cert = "file:///etc/certs/<YOUR_DEVICE_CERT>-full-chain.cert.pem"
        - uncomment pk = "file:///etc/certs/<YOUR_DEVICE_CERT>.key.pem"
    - Save and close nano

9. Apply the configuration and restart IoT Edge runtime by executing the following command in SSH shell
    ```Linux
    sudo iotedge config apply
    ```
10. Check IoT Edge status
    ```Linux
    sudo iotedge list
    ```
11. Reboot the VM to refresh the IoT Edge binding
    ```Linux
    sudo reboot
    ```
