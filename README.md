
## Running A100-Spot VM on Azure
```
sudo apt update
sudo apt install python3-venv
python3 -m venv .venv
Install Jupyter extension for the .venv to show up. 
```

### CUDA Instalation in Azure VM. 
```
sudo apt update && sudo apt install -y ubuntu-drivers-common

sudo ubuntu-drivers install

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo apt install -y ./cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt -y install cuda-toolkit-12-5
```

# Instagram scraping
1. doc_id changes everyday for Instagram.
2. Current scraping is done by hitting the Instagram web_profile_info URL in 1000 threads at a time. Need to change IP after doing this - i.e., reboot WiFi.
3. Another method that seems to work is the scrape_profile API with a random delay. However, Instagram blocks this after 30 requests with response code 401.
4. Instagram returns 429 when hitting the web_profile_info URL from free VPNs, Colab, Kaggle.

# Mounting azure blob storage on a VM:
## Installing blobfuse2 on VM:
1. sudo wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb
2. sudo dpkg -i packages-microsoft-prod.deb
3. sudo apt-get update
4. sudo apt-get install libfuse3-dev fuse3
5. sudo apt-get install blobfuse2

## Mounting container on VM:
1. sudo mkdir /ramdisk
2. sudo mount -t tmpfs -o size=16g tmpfs /ramdisk
3. sudo mkdir /ramdisk/blobfuse2tmp
4. sudo chown azureuser /ramdisk/blobfuse2tmp
5. mkdir ~/husnstorage
5. sudo blobfuse2 mount ~/mycontainer --config-file=./config.yaml --allow-other

These steps are usually needed at every reboot because the mount has been created as part of ram (tmpfs). But we have added a script (`/home/azureuser/mount_blobstorage.sh`) on the VM that automates these steps and it has been put into crontab @reboot.

Official specs:

1. https://learn.microsoft.com/en-us/azure/storage/blobs/blobfuse2-how-to-deploy?tabs=Ubuntu
2. https://learn.microsoft.com/en-us/azure/storage/blobs/network-file-system-protocol-support-how-to

## Transferring data from localhost to Azure blob storage;
1. brew install azcopy
2. azcopy copy `DIR_NAME` "`<STORAGE_ACCOUNT_ACCESS_KEY>`" --recursive=true