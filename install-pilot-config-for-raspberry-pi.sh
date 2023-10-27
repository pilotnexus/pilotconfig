#!/bin/bash

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "pipx not found! Installing pipx..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath

    # Update PATH directly for the current session to include pipx bin, in case .bashrc or .profile changes aren't sourced immediately
    export PATH="$PATH:$HOME/.local/bin"
fi

PILOT_PATH="$HOME/.local/bin/pilot"
PILOT_BACKUP="$PILOT_PATH"_original

# Always force reinstall 'pilot-config' to get the latest version and to avoid file collisions
pipx install pilot-config --force

# Check if the 'pilot' binary is present and non-empty
if [ ! -f $PILOT_PATH ] || [ ! -s $PILOT_PATH ]; then
    echo "Error: Unable to properly install or locate the pilot binary."
    exit 1
fi

# Check if the privilege escalation code is already present
if ! grep -q "Re-run the script with sudo" $PILOT_PATH; then
    # Backup the original pilot script
    cp $PILOT_PATH $PILOT_BACKUP

    # Insert the privilege escalation code right after the shebang
    sed '1a\
import os, sys\
\
# Check if we are running as root already.\
if os.geteuid() != 0:\
    # Re-run the script with sudo\
    os.execvp("sudo", ["sudo", sys.executable] + sys.argv)\
' $PILOT_BACKUP > $PILOT_PATH

    # Remove the backup
    rm $PILOT_BACKUP
fi

# Ensure that the pilot script is executable
chmod +x $PILOT_PATH

echo "Installation complete! Start using pilot-config by typing 'pilot setup'"
