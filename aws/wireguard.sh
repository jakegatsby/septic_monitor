#!/bin/bash

WGKEY=/etc/wireguard/private.key

test -f ${WGKEY} || wg genkey > ${WGKEY}
chmod 0400 ${WGKEY}
ip link add wg0 type wireguard
ip addr add 10.0.0.1/24 dev wg0
wg set wg0 listen-port 5182 private-key ${WGKEY}
ip link set wg0 up
