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

# Create a wrapper script to run the pilot-config tool with sudo
echo "#!/bin/bash
sudo ~/.local/bin/pilot \"\$@\"
" > ~/.local/bin/pilot

# Make the wrapper script executable
chmod +x ~/.local/bin/pilot

echo "Installation complete! Start using pilot-config by typing 'pilot setup'"
