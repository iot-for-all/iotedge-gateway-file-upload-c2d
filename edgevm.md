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
3. Install IoT Edge
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
5. Run the following command to create the **"files"** folder for saving the large payloads
    ```Linux
    sudo mkdir -p -v /etc/files
    sudo chmod 777 /etc/files
    ```
6. Provision IoT Edge with its cloud identity
    ```Linux
    sudo nano /etc/aziot/config.toml
    ```
    - under Manual provisioning with symmetric key:
        - uncomment [provisioning]
        - uncomment source = "manual"
        - uncomment connection_string = "<YOUR_REGISTERED_IOT_EDGE_CONNECTION_STRING>
    - Save and close nano

7. Apply the configuration and restart IoT Edge runtime by executing the following command in SSH shell
    ```Linux
    sudo iotedge config apply
    ```
8. Check IoT Edge status
    ```Linux
    sudo iotedge list
    ```
9. Reboot the VM to refresh the IoT Edge binding
    ```Linux
    sudo reboot
    ```
