
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
