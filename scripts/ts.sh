#!/bin/bash
# In The Name of God
# ========================================
# [] File Name : ts.sh
#
# [] Creation Date : 18-05-2021
#
# [] Created By : Parham Alvani <parham.alvani@gmail.com>
# =======================================

# shellcheck disable=2034
dependencies="node"

usage() {
	echo -n "typescript at you door"
	# shellcheck disable=2016
	echo '
 _                             _       _
| |_ _   _ _ __  ___  ___ _ __(_)_ __ | |_
| __| | | | |_ \/ __|/ __| |__| | |_ \| __|
| |_| |_| | |_) \__ \ (__| |  | | |_) | |_
 \__|\__, | .__/|___/\___|_|  |_| .__/ \__|
     |___/|_|                   |_|
	'
}

main() {
	sudo npm install -g typescript

	msg "$(tsc --version)"
}
