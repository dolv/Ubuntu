BEGIN {
FS= "[ /]"; sensors_num=0
}
{
if ( NR == FNR ){
    sensors[$1] = $2
    totals[$1] = 0
    avg[$1]=0
}else{ 
    totals[$2] += 1; 
    avg[$2] += $3}
}
END {
    for (key in avg) avg[key] /= totals[key]
    asort(avg, dest)
    for (key in avg)
        for (i in dest)
            if (dest[i] == avg[key] && key!="") printf "%-15s %4.0f\n", sensors[key], avg[key]
}
