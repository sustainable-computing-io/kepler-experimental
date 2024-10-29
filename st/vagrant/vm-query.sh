#!/usr/bin/env bash

set -eu -o pipefail

main() {
	while true; do
		http ':9090/api/v1/query' \
			'query==irate(kepler_node_package_joules_total{job="vm"}[8s])' |
			jq -r ' (now | strftime("%Y-%m-%d %H:%M:%S") ) + "  " + (.data.result[] | .metric.job + ": " + (.value[1]|tostring))'
		sleep 3.1
	done

}

main "$@"
