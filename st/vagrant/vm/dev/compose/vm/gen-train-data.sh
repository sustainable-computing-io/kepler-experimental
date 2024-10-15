#!/usr/bin/env bash

set -euo pipefail

trap exit_all INT

exit_all() {
	pkill -P $$
}

echo_e() {
	echo -e "$*" >&2
}

run() {
	echo_e " ❯ $*\n"
	${DRY_RUN:-false} && return 0

	local -i ret=0
	"$@"
	ret=$?
	return $ret
}

run_stress() {
	local n=${1}
	local cpus=${2}
	shift 2

	local load_curve=(${@})

	# stress-ng --cpu 32 --iomix 4 --vm 2 --vm-bytes 128M --fork 4 --timeout 10s
	for i in $(seq 1 "$n"); do
		echo "❃ [$cpu/$cpus]:  $i / $n"
		echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

		for x in "${load_curve[@]}"; do
			local load="${x%%:*}"
			local time="${x##*:}s"
			run stress-ng \
				--cpu-method ackermann \
				--cpu "$cpu" \
				--cpu-load "$load" \
				--timeout "$time"

			echo_e "   ──────────────────────────────────────────── ❃ [$cpu/$cpus]:  $i / $n"
		done
	done
}

main() {
	local n=${1:-1}
	shift || true

	local cpus
	cpus=$(nproc)

	local -a train_data=(
		0:10
		5:10
		10:10
		15:10
		20:10
		25:10
		30:10
		35:10
		40:10
		45:10
		50:10
		55:10
		60:10
		65:10
		70:10
		75:10
		80:10
		85:10
		90:10
		95:10
		100:10
	)

	local started_at
	started_at=$(date +%s)
	run sleep 5
	for cpu in $(seq 1 "$cpus"); do
		run_stress "$n" "$cpu" "${train_data[@]}"
	done

	local -a test_data=(
		0:5
		10:5
		20:5
		30:5
		40:5
		50:5
		60:5
		70:5
		80:5
		90:5
		100:5
	)

	for cpu in $(seq 1 "$cpus"); do
		run_stress "$n" "$cpu" "${test_data[@]}"
	done
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	run sleep 5

	local ended_at
	ended_at=$(date +%s)

	local elapsed=$((ended_at - started_at))
	echo "Loops: $n"
	echo "started at: $started_at  " "$(date -u -d "@$started_at" +'%Y-%m-%dT%H:%M:%SZ')"
	echo "ended   at: $ended_at  " "$(date -u -d "@$ended_at" +'%Y-%m-%dT%H:%M:%SZ')"
	echo "elapsed   : $elapsed seconds"

}
# main() {
# 	local n=${1:-1}
# 	shift || true
#
# 	local cpus
# 	cpus=$(nproc)
#
# 	local -a load_curve=(
# 		0:10
# 		5:10
# 		10:10
# 		15:10
# 		20:10
# 		25:10
# 		30:10
# 		35:10
# 		40:10
# 		45:10
# 		50:10
# 		55:10
# 		60:10
# 		65:10
# 		70:10
# 		75:10
# 		80:10
# 		85:10
# 		90:10
# 		95:10
# 		100:10
# 	)
#
# 	local started_at
# 	started_at=$(date +%s)
#
# 	# stress-ng --cpu 32 --iomix 4 --vm 2 --vm-bytes 128M --fork 4 --timeout 10s
# 	for cpu in $(seq 1 "$cpus"); do
# 		for i in $(seq 1 "$n"); do
# 			echo "❃ [$cpu/$cpus]:  $i / $n"
# 			echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
#
# 			for x in "${load_curve[@]}"; do
# 				local load="${x%%:*}"
# 				local time="${x##*:}s"
# 				run stress-ng \
# 					--cpu-method ackermann \
# 					--cpu "$cpu" \
# 					--cpu-load "$load" \
# 					--timeout "$time"
#
# 				echo_e "   ──────────────────────────────────────────── ❃ [$cpu/$cpus]:  $i / $n"
# 			done
# 		done
# 	done
# 	echo
# 	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# 	sleep 10
#
# 	local ended_at
# 	ended_at=$(date +%s)
#
# 	local elapsed=$((ended_at - started_at))
# 	echo "Loops: $n"
# 	echo "started at: $started_at  " "$(date -u -d "@$started_at" +'%Y-%m-%dT%H:%M:%SZ')"
# 	echo "ended   at: $ended_at  " "$(date -u -d "@$ended_at" +'%Y-%m-%dT%H:%M:%SZ')"
# 	echo "elapsed   : $elapsed seconds"
# }

main "$@"
