#!/bin/sh
set -e
# Pass through to surge CLI; default is scheduler mode
exec "$@"
