#!/bin/bash
readonly PROGRNAME=$(basename $0)
readonly PROGDIR=$(readlink -m $(dirname $0))
readonly ARGS="$@"
readonly PREFIX="/usr/bin"

increase_original_zone_serial() {
	local zone=$1
	${PREFIX}/ldns-read-zone -S YYYYMMDDxx ${zone} > ${zone}.tmp
	mv ${zone}.tmp ${zone}
}

increase_zone_serial_from_signed() {
	local zone=$1
	${PREFIX}/ldns-read-zone -S YYYYMMDDxx ${zone}.signed > ${zone}
}

sign_zone() {
	local zone=$1
	# Expire in one month +2 days (instead of the annoying three week default)
	#local expire=`date -v+1m -v+2d "+%Y%m%d"`
	# Linux date is strange, but accepts this:
	local expire=`date -d "1 month 2 days" "+%Y%m%d"`
	local keys=$(find_keys_for_zone $zone)

	${PREFIX}/ldns-signzone -e $expire $zone $keys
}

find_keys_for_zone() {
	local zone=$1
	local zonedir=$(dirname $zone)
	local zonename=$(basename $zone)
	zonename=${zonename%.zone}
	local keys=`ls ${zonedir}/K${zonename}.+*.private`
	keys=${keys//.private/}
	echo $keys
}

is_writable_file() {
	local file=$1
	
	[[ -w $file ]]
}

check_zone() {
    local zone=$1
    if ${PREFIX}/ldns-read-zone $zone > /dev/null
        then pass
        else exit 1
    fi
}

usage () {
	cat <<- EOF
	usage: $PROGNAME zonefile

	This program uses the ldns toolkit installed in ${PREFIX} to sign a zone file.
	It first increments the zone serial, and then signs the zone.
	The expiry is set to one month plus two days, to allow for easier crontab integration,
	with some leeway for possible failures.
	EOF
}

main() {
	zone=$ARGS
	echo "Signing ${zone}.."
	check_zone $zone
	if is_writable_file ${zone}.signed; then
		increase_zone_serial_from_signed $zone	
	else
		increase_original_zone_serial $zone
	fi
	sign_zone $zone
#	find_keys_for_zone $ARGS
}
main
