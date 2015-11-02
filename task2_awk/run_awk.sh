#!/bin/bash
echo "---=== Solution 1 ===---"
awk -f script_awk.sh sensors readings
echo "---=== Solution 2 ===---"
awk -f script_awk2.sh sensors readings
