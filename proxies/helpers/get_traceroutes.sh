#!/usr/bin/env sh

FILE='router_ips'

cat $FILE | while read line
do
#echo $line
traceroute $line >> traceroute.out 2>&1
done