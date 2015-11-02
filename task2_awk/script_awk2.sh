BEGIN { FS="[ /]" }
/^[0-9]+ \w[a-zA-Z]*[ \s]*$/  {sensors[$1] = $2}
/^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}\/[0-9]+\/[0-9]+[ \s]*$/ {totals[$2] +=1;avg[$2] += $3}
END {for (key in avg) avg[key] /= totals[key]
    asort(avg, dest)
    for (i in dest)
        for (key in avg)
            if (dest[i] == avg[key] && key != "") printf "%-15s %4.0f\n", sensors[key], avg[key]}
