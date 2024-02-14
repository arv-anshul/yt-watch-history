#!/bin/bash

# Infer requirements.txt for each `backend` and `frontend` apps from `requirements.lock`

lockfile=$1
txtfile=$2

if [[ -z $txtfile || -z $lockfile ]]; then
    echo "Both txtfile and lockfile exist! Make sure you pass only one argument."
    exit 1
fi

# Check if passed files exists
if [[ ! -f $txtfile || ! -f $lockfile ]]; then
    echo "'$txtfile' not found!"
    exit 1
fi

# Read requirements.lock and update requirements.txt
while IFS= read -r line || [[ -n "$line" ]]; do
    # Extract package and version using awk
    read -r package version <<< "$(awk -F '==' '{print $1, $2}' <<< "$line")"

    # Check if the package is already present in requirements.txt
    grep -q "^$package==" $txtfile
    if [ $? -eq 0 ]; then
        # Update the version in requirements.txt
        sed -i.bak "s/^$package==.*$/$package==$version/" "$txtfile"
    fi
done < $lockfile

# Delete the backup file of "$txtfile"
if [ -f "$txtfile.bak" ]; then
    rm "$txtfile.bak"
fi

echo "Updated $txtfile with versions from $lockfile"
