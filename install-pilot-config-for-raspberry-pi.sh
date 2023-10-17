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

# Modify the ~/.local/bin/pilot script to include the sudo check and rerun
sed -i '5i\
# Check if we\'re running as root already.\
if os.geteuid() != 0:\
    # Re-run the script with sudo\
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)\
' ~/.local/bin/pilot

echo "Installation complete! Start using pilot-config by typing 'pilot setup'"
