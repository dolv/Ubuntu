#!/bin/bash
#echo "Ukraine          Kyiv  Kharkiv" | sed 's%^\([[:alnum:]]\+\)\([   ]*\)\([[:alnum:]]\+\)%\3\2\1%'
#echo "Ukraine          Kyiv  Kharkiv" | sed 's%^\(\w\+\)\([   ]*\)\(\w\+\)%\3\2\1%'
# | awk '{printf "%1d %15-s %s \%\%%15-s %s\n", $1 ,$2, $3, $4 ,$5}'

sed 's/\(\(^\w\+\).\(\w\+\)\)/\1 => \3 \2/g' sensors
