#!/bin/bash

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "pipx not found! Installing pipx..."
    sudo apt install -y pipx
    pipx ensurepath
    # Reload shell to ensure new path is active
    source ~/.bashrc
fi

# Install your tool with pipx
pipx install pilot-config

# Backup the original pilot script
cp ~/.local/bin/pilot ~/.local/bin/pilot_original

# Create a new pilot script with sudo check and re-run capability
echo '#!/usr/bin/env python3' > ~/.local/bin/pilot
echo 'import os, sys' >> ~/.local/bin/pilot
echo '' >> ~/.local/bin/pilot
echo '# Check if we are running as root already.' >> ~/.local/bin/pilot
echo 'if os.geteuid() != 0:' >> ~/.local/bin/pilot
echo '    # Re-run the script with sudo' >> ~/.local/bin/pilot
echo '    os.execvp("sudo", ["sudo", sys.executable, sys.argv[0]] + sys.argv[1:])' >> ~/.local/bin/pilot
echo '' >> ~/.local/bin/pilot
cat ~/.local/bin/pilot_original >> ~/.local/bin/pilot

# Remove the backup
rm ~/.local/bin/pilot_original

# Ensure that the pilot script is executable
chmod +x ~/.local/bin/pilot

echo "Installation complete! Start using pilot-config by typing 'pilot setup'"
