
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