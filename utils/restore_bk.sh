#!/bin/bash

# Restores backup

set -e

if [ -z "$1" ]; then
	echo "Usage: ./utils/restore_bk.sh path/to/backup.sql"
	exit 1
fi

BKFILE=$1

if [[ ! -f "$BKFILE" ]]; then
	echo "No such file: $BKFILE"
	exit 1
fi

if [[ "$BKFILE" == *.gpg ]]; then
	IN=$BKFILE
	BKFILE=/tmp/$(basename "$BKFILE" .gpg)
	echo "Decrypting backup at $IN to $BKFILE"
	gpg --decrypt "$IN" > "$BKFILE"
fi

echo "Importing backup from $BKFILE"
cat $BKFILE | docker exec -i contentdb_db_1 psql contentdb contentdb
