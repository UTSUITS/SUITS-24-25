#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Updating system packages..."
sudo apt update
sudo apt full-upgrade -y

echo "Installing base packages (Python, pip, Redis, Git, Docker)..."
# Install Python 3.11 and pip
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Redis server
sudo apt install -y redis-server

# Install Git
sudo apt install -y git

# Install Docker
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group (so you don't need sudo to run docker commands)
sudo usermod -aG docker $USER

# Install Flask (globally, just in case)
sudo apt install python3-flask python3-redis python3-matplotlib 

# Installing pyqt6 dependencies 
sudo apt install ninja-build libfontconfig1-dev libdbus-1-dev libfreetype6-dev libicu-dev libinput-dev libxkbcommon-dev libsqlite3-dev libssl-dev libpng-dev libjpeg-dev libglib2.0-dev libgles2-mesa-dev libgbm-dev libdrm-dev libx11-dev libxcb1-dev libxext-dev libxi-dev libxcomposite-dev libxcursor-dev libxtst-dev libxrandr-dev libx11-xcb-dev libxext-dev libxfixes-dev libxi-dev libxrender-dev libxcb1-dev libxcb-glx0-dev libxcb-keysyms1-dev libxcb-image0-dev libxcb-shm0-dev libxcb-icccm4-dev libxcb-sync-dev libxcb-xfixes0-dev libxcb-shape0-dev libxcb-randr0-dev libxcb-render-util0-dev libxcb-util0-dev libxcb-xinerama0-dev libxcb-xkb-dev libxkbcommon-dev libxkbcommon-x11-dev libxcb-xinput-dev

echo "Setting up Python virtual environment..."
# Create a project directory if needed
mkdir -p ~/Projects
cd ~/Projects

# Make a virtual environment
python3.11 -m venv pi_venv

# Activate it
source ~/Projects/pi_venv/bin/activate

echo "Upgrading pip and installing Python packages inside venv..."
pip install --upgrade pip
pip install flask redis PyQt6

echo "Installing Tailscale..."
# Install Tailscale the official way
curl -fsSL https://tailscale.com/install.sh | sh

echo ""
echo "All done!"
echo ""
echo ">>> REMEMBER: To activate your virtual environment later, run:"
echo "    source ~/Projects/pi_venv/bin/activate"
echo ""
echo ">>> You may also need to reboot for Docker group permissions to apply:"
echo "    sudo reboot"
