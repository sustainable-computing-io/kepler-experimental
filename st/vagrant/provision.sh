#!/usr/bin/env bash
set -euo pipefail

is_fn() {
	[[ $(type -t "$1") == "function" ]]
	return $?
}

echo_e() {
	echo -e "$*" >&2
}

echo_en() {
	echo -en "$*" >&2
}
info() {
	echo_e " 🔔 $*"
}

ok() {
	echo_e " ✅ $*"
}

warn() {
	echo_e " ⚠️  $*"
}

skip() {
	echo_e " 🙈 SKIP: $*"
}

die() {
	echo_e "\n ✋ $* "
	echo_e "──────────────────── ⛔️⛔️⛔️ ────────────────────────\n"
	exit 1
}

line() {
	local len="$1"
	shift

	echo_en "────"
	printf '─%.0s' $(seq "$len") >&2
	echo_e "────────"
}

header() {
	local title="🔆🔆🔆  $*  🔆🔆🔆 "

	local len=40
	if [[ ${#title} -gt $len ]]; then
		len=${#title}
	fi

	echo_e "\n\n  \033[1m${title}\033[0m"
	echo_e -n "━━━━━"
	printf '━%.0s' $(seq "$len") >&2
	echo_e "━━━━━━━"

}

debug() {
	${DEBUG:-false} || return
	echo_e " 🧙 $*"
}

pick_one() {
	for x in "$@"; do echo "$x"; done | fzf --no-clear
}

run() {
	echo_e " ❯ $*\n"

	if ${DRY_RUN:-false}; then
		return 0
	fi

	local -i ret=$?
	if [[ "$*" =~ \| ]]; then
		bash -c "$@"
		ret=$?
	else
		"$@"
		ret=$?
	fi

	echo_e "        ────────────────────────────────────────────\n"
	return $ret
}

trim() {
	local var="$*"
	# remove leading whitespace characters
	var="${var#"${var%%[![:space:]]*}"}"
	# remove trailing whitespace characters
	var="${var%"${var##*[![:space:]]}"}"
	printf '%s' "$var"
}

array_contains() {
	local what="$1"
	shift

	for x in "$@"; do
		[[ "$what" == "$x" ]] && return 0
	done
	return 1
}

install() {
	run sudo dnf install -y "$@"
}

main() {

	info "provision.sh"
	dnf install -y cloud-utils-growpart
	sudo cfdisk
	sudo btrfs filesystem resize max /

}

main "$@"
