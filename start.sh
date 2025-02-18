#!/bin/bash
# In The Name of God
# ========================================
# [] File Name : start.sh
#
# [] Creation Date : 17-07-2018
#
# [] Created By : Parham Alvani <parham.alvani@gmail.com>
# =======================================
# https://stackoverflow.com/questions/3822621/how-to-exit-if-a-command-failed
set -e

# global variable that points to dotfiles root directory
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/message.sh
source "$current_dir/scripts/lib/message.sh"
# shellcheck source=scripts/lib/proxy.sh
source "$current_dir/scripts/lib/proxy.sh"
# shellcheck source=scripts/lib/linker.sh
source "$current_dir/scripts/lib/linker.sh"

# start.sh
program_name=$0

trap '_end' INT

_end() {
	echo "see you later :) [you signal start.sh execuation]"
	exit
}

_usage() {
	echo ""
	echo "usage: $program_name [-y] [-h] [-f] script [script options]"
	echo "  -f   force"
	echo "  -h   display help"
	echo "  -d   as dependency (internal usage)"
	echo "  -y   yes to all"
	echo ""
}

_main() {
	## global variables ##

	# global variable indicates force in specific script and runs script with root
	local force=false

	# global variable indicates show help for user in specific script
	# there is no need to use it in your script
	local show_help=false

	# ask no questions, use sane defaults
	local yes_to_all=false

	# as_dependency shows that this start.sh is going to install a dependency
	local as_dependency=false

	# parses options flags
	while getopts 'fdhy' argv; do
		case $argv in
		h)
			show_help=true
			;;
		f)
			force=true
			;;
		d)
			as_dependency=true
			;;
		y)
			yes_to_all=true
			;;
		*)
			_usage
			;;
		esac
	done

	for ((i = 2; i <= OPTIND; i++)); do
		shift
	done

	if [ $as_dependency = false ]; then
		# shellcheck source=scripts/lib/header.sh
		source "$current_dir/scripts/lib/header.sh"
	fi

	# handles root user
	if [[ $EUID -eq 0 ]]; then
		message "pre" "it must run without the root permissions with a regular user."
		if [ $force = false ]; then
			exit 1
		fi
	fi

	# handles given script run and result
	local script
	local start
	local took

	if [ -z "$1" ]; then
		_usage
		exit
	fi
	script=$1
	shift

	start=$(date +'%s')

	# shellcheck disable=1090
	source "$current_dir/scripts/$script.sh" 2>/dev/null || {
		echo "404 script not found"
		exit
	}
	if [ $show_help = true ]; then
		# prints the start.sh and the script helps
		_usage
		echo
		usage
	else
		# run the script
		msg() { message "$script" "$@"; }
		msg "$(usage)"

		# handle dependencies by executing the start.sh
		# multiple times
		dependencies=${dependencies:-""}
		_dependencies "$dependencies"

		run "$@"
	fi

	echo
	took=$(($(date +'%s') - start))
	printf "done. it took %d seconds.\n" $took
}

_dependencies() {
	dependencies=$1

	if [ -z "$dependencies" ]; then
		return
	fi

	msg "dependencies: $dependencies"

	if [ $yes_to_all = true ]; then
		accept="Y"
	else
		read -r -p "[$script] do you want to install dependencies?[Y/n] " -n 1 accept
		echo
	fi

	if [[ $accept == "Y" ]]; then
		local options="-d"
		if [ $yes_to_all = true ]; then
			options="$options -y"
		fi

		for dependency in $dependencies; do
			"$current_dir/start.sh" "$options" "$dependency"
		done
	fi
}

run() {
	install

	# run the script
	if declare -f main >/dev/null; then
		main "$@"
	else
		msg "main not found"
	fi
}

install() {
	if [[ "$OSTYPE" == "darwin"* ]]; then
		msg "darwin with brew (osx?)"

		if declare -f main_brew >/dev/null; then
			main_brew
		else
			msg "main_brew not found"
		fi

		return
	fi

	if [[ "$(command -v brew)" ]]; then
		msg "linux with brew (ubuntu?)"

		if declare -f main_brew >/dev/null; then
			if [ $yes_to_all = true ]; then
				install_with_brew="n"
			else
				read -r -p "[$script] do you want to install with brew?[Y/n] " -n 1 install_with_brew
				echo
			fi

			if [[ $install_with_brew == "Y" ]]; then
				# brew installation on linux is optional
				main_brew
				return
			fi
		else
			msg "main_brew not found"
		fi
	fi

	if [[ "$(command -v apt)" ]]; then
		msg "linux with apt (ubuntu?)"

		if declare -f main_apt >/dev/null; then
			main_apt
		else
			msg "main_apt not found"
		fi

		return
	fi

	if [[ "$(command -v pacman)" ]]; then
		msg "linux with pacman (arch!)"

		if declare -f main_pacman >/dev/null; then
			main_pacman
		else
			msg "main_pacman not found"
		fi

		return
	fi
}

_main "$@"
