#!/bin/bash 
# https://pouta.csc.fi/dashboard/project/containers/container/arvodev
# https://docs.csc.fi/data/Allas/introduction/
# ..chmod +x find_s3cfg.sh
# ..or just in terminal: S3CFG_PATH="$HOME/.s3cfg"; if [ -f "$S3CFG_PATH" ]; then echo "Found .s3cfg file at: $S3CFG_PATH"; echo "Displaying contents:"; cat "$S3CFG_PATH"; else echo "The .s3cfg file does not exist."; fi
# ..or just for keys grep key $HOME/.s3cfg

# Define the .s3cfg file path in the home directory
S3CFG_PATH="$HOME/.s3cfg"

# Check if the .s3cfg file exists and then display its contents
if [ -f "$S3CFG_PATH" ]; then
    echo "Found .s3cfg file at: $S3CFG_PATH"
    echo "Displaying contents:"
    cat "$S3CFG_PATH"
else
    echo "The .s3cfg file does not exist."
fi