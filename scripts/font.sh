#!/bin/bash
# In The Name of God
# ========================================
# [] File Name : sample.sh
#
# [] Creation Date : 17-07-2018
#
# [] Created By : Parham Alvani <parham.alvani@gmail.com>
# =======================================

usage() {
	echo "fonts for terminal, subtitles and more"
	echo '
  __             _
 / _| ___  _ __ | |_
| |_ / _ \| |_ \| __|
|  _| (_) | | | | |_
|_|  \___/|_| |_|\__|

  '
}

if [[ $(uname) == 'Darwin' ]]; then
	# MacOS
	font_dir="$HOME/Library/Fonts"
else
	# Linux
	font_dir="$HOME/.local/share/fonts"
	if [ ! -d "$HOME/.local/share/fonts" ]; then
		mkdir -p "$font_dir"
	fi
fi

_install_jetbrains() {
	if fc-list -q 'JetBrains Mono'; then
		msg "you have the jetbrains mono installed"
	else
		jbm_version="2.225"
		msg "install jetbrains mono ($jbm_version) by dowloading its archive"

		rm "JetBrainsMono-$jbm_version.zip" || true
		rm -Rf jb || true

		wget "https://download.jetbrains.com/fonts/JetBrainsMono-$jbm_version.zip"
		unzip "JetBrainsMono-$jbm_version.zip" -d jb && rm "JetBrainsMono-$jbm_version.zip"

		mv jb/fonts/ttf/* "$font_dir" && rm -Rf jb
	fi
}

_install_vazir_code() {
	if fc-list -q 'Vazir Code'; then
		msg "you have the vazir code installed"
	else
		vzc_version="1.1.2"
		msg "install vazir code ($vzc_version) by downloading its archive"

		rm "vazir-code-font-v$vzc_version.zip" || true
		rm -Rf vzc || true

		wget "https://github.com/rastikerdar/vazir-code-font/releases/download/v$vzc_version/vazir-code-font-v$vzc_version.zip"
		unzip "vazir-code-font-v$vzc_version.zip" -d vzc && rm "vazir-code-font-v$vzc_version.zip"

		mv vzc/Vazir-Code.ttf "$font_dir" && rm -Rf vzc
	fi
}

_install_vazir_thin() {
	if fc-list -q 'Vazir Thin'; then
		msg "you have the vazir thin installed"
	else
		v_version="29.1.0"
		wget "https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v$v_version/dist/Vazir-Thin.ttf"
		mv Vazir-Thin.ttf "$font_dir"
	fi
}

main_brew() {
	brew install --cask homebrew/cask-fonts/font-jetbrains-mono
	brew install --cask homebrew/cask-fonts/font-jetbrains-mono-nerd-font

	_install_vazir_thin
}

main_pacman() {
	sudo pacman -Syu --needed --noconfirm noto-fonts-emoji ttf-roboto ttf-jetbrains-mono ttf-font-awesome ttf-dejavu noto-fonts
	yay -Syu --needed vazir-fonts
	yay -Syu --needed vazir-code-fonts
	yay -Syu --needed nerd-fonts-jetbrains-mono
}

main_apt() {
	msg 'install roboto font from apt repository'
	sudo apt-get install fonts-roboto

	_install_jetbrains

	_install_vazir_thin

	_install_vazir_code
}
