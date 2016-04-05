#!/usr/bin/env sh

FILE='ips'

cat $FILE | while read line
do
#echo $line
ping -c 3 $line >> ping.out 2>&1
done