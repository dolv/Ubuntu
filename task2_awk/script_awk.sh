BEGIN {
FS= "[ /]"
sensors_num=0
}

{
if ( NR == FNR ){
    sensors[$1] = $2
    sensors_num += 1
    totals[$1] = 0
    avg[$2]=0
}else 
    totals[$2] += $3
}

END {
    for (sensor in sensors)
        for (a in avg) 
            if (sensors[sensor] == a) avg[a] = totals[sensor]/sensors_num
    asort(avg, dest)
    for (i in dest)
        for (key in avg)
            if (dest[i] == avg[key]) printf "%-15s %4.1f\n", key, avg[key]
}
