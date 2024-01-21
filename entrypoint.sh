#!/bin/sh

# Start lircd daemon
lircd
# Run commands
exec "$@"
