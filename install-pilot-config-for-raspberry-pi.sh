#!/bin/bash

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "pipx not found! Installing pipx..."
    sudo apt install -y pipx
    python3 -m pipx ensurepath
    # Reload shell to ensure new path is active
    source ~/.bashrc
fi

# Install your tool with pipx
pipx install pilot-config

# Backup the original pilot script
cp ~/.local/bin/pilot ~/.local/bin/pilot_original

# Insert the privilege escalation code right after the shebang
sed '1a\
import os, sys\
\
# Check if we are running as root already.\
if os.geteuid() != 0:\
    # Re-run the script with sudo\
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)\
' ~/.local/bin/pilot_original > ~/.local/bin/pilot

# Remove the backup
rm ~/.local/bin/pilot_original

# Ensure that the pilot script is executable
chmod +x ~/.local/bin/pilot

echo "Installation complete! Start using pilot-config by typing 'pilot setup'"
