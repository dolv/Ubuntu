#!/bin/bash
time_limit=600 # seconds
START_COPYING_TIME=$(date +%s)
    trigger=0
    while [ trigger ]
    do
        time_dif=$(( $(date +%s)-$START_COPYING_TIME ))
        [ $time_limit -gt $time_dif ] || trigger=1 
        if [ $(( time_dif % 2)) -eq 0 ]; then
            printf "\ttik\n"
        else 
            printf "\ttak\n"
        fi
        sleep 1s
    done  
