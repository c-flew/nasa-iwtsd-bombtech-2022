#!/usr/bin/bash

while ! ping -I eth0 -c1 1.1.1.1 &> /dev/null; do
    sleep 0.2
done

/usr/bin/wg-quick up wg0
