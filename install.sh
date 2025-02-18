#!/bin/bash
# In The Name Of God
# ========================================
# [] File Name : install.sh
#
# [] Creation Date : 09-07-2016
#
# [] Created By : Parham Alvani (parham.alvani@gmail.com)
# =======================================
set -e
program_name=$0

usage() {
	echo "usage: $program_name [-h] [-y]"
	echo "  -y   yes to all"
	echo "  -h   display help"
}

# global variable that points to dotfiles root directory
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/lib/message.sh
source "$current_dir/scripts/lib/message.sh"
# shellcheck source=scripts/lib/linker.sh
source "$current_dir/scripts/lib/linker.sh"
# shellcheck source=scripts/lib/header.sh
source "$current_dir/scripts/lib/header.sh"

message "pre" "Home directory found at $HOME"

message "pre" "Current directory found at $current_dir"

yes_to_all=0
while getopts "hy" argv; do
	case $argv in
	y)
		yes_to_all=1
		;;
	*)
		usage
		exit
		;;
	esac
done

requirements=(zsh tmux vim nvim)

# check the existence of required softwares
for cmd in "${requirements[@]}"; do
	if ! hash "$cmd" 2>/dev/null; then
		message "pre" "Please install $cmd before using this script"
		exit 1
	fi
done

# vim
install-vim() {
	dotfile "vim" "vimrc"
}

# nvim
install-nvim() {
	nvim_version="$(nvim -v | head -1 | cut -d' ' -f2)"

	if [[ "$nvim_version" > 'v0.5.0' ]] || [[ "$nvim_version" == 'v0.5.0' ]]; then
		configfile "nvim" "" "nvim/nvim5"
	else
		configfile "nvim" "" "nvim/nvim4"
	fi
}

# configurations
install-conf() {
	dotfile "conf" "dircolors"
	dotfile "conf" "aria2"
	configfile "htop" "" "conf"
}

# wakatime
install-wakatime() {
	dotfile "wakatime" "wakatime.cfg"
}

# tmux
install-tmux() {
	dotfile "tmux" 'tmux.conf'

	message "tmux" "installing tmux plugins"
	if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
		mkdir -p ~/.tmux/plugins
		git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
	fi
	~/.tmux/plugins/tpm/bin/install_plugins
}

# zsh
install-zsh() {
	dotfile "zsh" "zshrc"
	dotfile "zsh" "zshenv"
	dotfile "zsh" "zsh.plug"
}

# git
install-git() {
	configfile "git"
}

# bin
install-bin() {
	dotfile "bin" "bin" false
}

# general
install-general() {
	if [ "$SHELL" != '/bin/zsh' ]; then
		message "general" "please change your shell to zsh manually"
	fi
}

# calls each module's install function.
modules=(conf tmux wakatime zsh git vim nvim bin general)
for module in "${modules[@]}"; do
	message "$module" "---"
	echo
	install-"$module"
	echo
	message "$module" "---"
	echo
done

announce "post" "thank you for using Parham Alvani dotfiles ! :)"
announce "post" "use *r* for reload your zshrc in place"
