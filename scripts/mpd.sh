#!/bin/bash
# In The Name of God
# ========================================
# [] File Name : mpd.sh
#
# [] Creation Date : 12-04-2021
#
# [] Created By : Parham Alvani <parham.alvani@gmail.com>
# =======================================

usage() {
	echo "mpd music server with ncmpcpp as a client"
	# shellcheck disable=2016
	echo '
                     _
 _ __ ___  _ __   __| |
| |_ ` _ \| "_ \ / _` |
| | | | | | |_) | (_| |
|_| |_| |_| .__/ \__,_|
          |_|
  '
}

main_brew() {
	return 1
}

main_apt() {
	return 1
}

main_pacman() {
	sudo pacman -Syu --noconfirm --needed mpd ncmpcpp mpc
}

main() {
	configfile mpd mpd.conf mpd
	systemctl --user enable mpd.service
	systemctl --user start mpd.service
}
