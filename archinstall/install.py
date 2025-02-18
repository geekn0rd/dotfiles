"""
Guided installation baed on archlinux/archinstall.
"""
import json
import logging
import os
import sys
import time

import archinstall
from archinstall.lib.general import run_custom_user_commands
from archinstall.lib.hardware import *
from archinstall.lib.networking import check_mirror_reachable
from archinstall.lib.profiles import Profile

if archinstall.arguments.get("help"):
    print("See `man archinstall` for help.")
    sys.exit(0)
if os.getuid() != 0:
    print("Archinstall requires root privileges to run. See --help for more.")
    sys.exit(1)

# For support reasons, we'll log the disk layout pre installation to
# match against post-installation layout
archinstall.log(
    f"Disk states before installing: {archinstall.disk_layouts()}",
    level=logging.DEBUG,
)


def defaults():
    """
    setup the default values.
    """
    archinstall.arguments["sys-language"] = archinstall.arguments.get(
        "sys-language", "en_US"
    )
    archinstall.arguments["sys-encoding"] = archinstall.arguments.get(
        "sys-encoding", "utf-8"
    )

    mirrors = archinstall.list_mirrors()
    archinstall.arguments["mirror-region"] = {"Iran": mirrors["Iran"]}
    archinstall.arguments["profile"] = "i3"
    archinstall.arguments["kernels"] = ["linux"]
    archinstall.arguments["nic"] = {"NetworkManager": True}
    archinstall.arguments["ntp"] = True
    archinstall.arguments["audio"] = "pipewire"
    archinstall.arguments["timezone"] = "Asia/Tehran"
    archinstall.arguments["keyboard-language"] = "us"
    archinstall.arguments["packages"] = (
        [
            "git",
            "wget",
            "curl",
            "v2ray",
            "neovim",
            "zsh",
            "python-pynvim",
            "python",
            "python-pip",
            "kitty",
            "base-devel",
            "xorg",
            "go",
            "alacritty",
            "xdg-utils",
        ]
        + ([
            "lightdm",
            "lightdm-gtk-greeter",
        ]
        if archinstall.arguments["profile"] == "i3"
        else ["gdm"]
        if archinstall.arguments["profile"] == "gnome"
        else ["sddm"]
        if archinstall.arguments["profile"] == "sway"
        else [])
    )

    archinstall.arguments["custom-commands"] = [
        "cd /home/parham; git clone https://aur.archlinux.org/yay-bin.git",
        "chown -R parham:parham /home/parham/yay-bin",
        "cd /home/parham; git clone https://github.com/1995parham/dotfiles.git",
        "chown -R parham:parham /home/parham/dotfiles",
    ]

    # archinstall.arguments["services"] = ["lightdm"]


def ask_user_questions():
    """
    setup disk layout and then continue the installation.
    """

    # Ask which harddrive/block-device we will install to
    archinstall.arguments["harddrive"] = archinstall.select_disk(
        archinstall.all_disks()
    )
    if archinstall.arguments["harddrive"] is None:
        archinstall.arguments["target-mount"] = archinstall.storage.get(
            "MOUNT_POINT", "/mnt"
        )

    # Perform a quick sanity check on the selected harddrive.
    # 1. Check if it has partitions
    # 3. Check that we support the current partitions
    # 2. If so, ask if we should keep them or wipe everything
    if (
        archinstall.arguments["harddrive"]
        and archinstall.arguments["harddrive"].has_partitions()
    ):
        archinstall.log(
            f"{archinstall.arguments['harddrive']} contains the following partitions:",
            fg="yellow",
        )

        # We curate a list pf supported partitions
        # and print those that we don't support.
        partition_mountpoints = {}
        for partition in archinstall.arguments["harddrive"]:
            try:
                if partition.filesystem_supported():
                    archinstall.log(f" {partition}")
                    partition_mountpoints[partition] = None
            except archinstall.UnknownFilesystemFormat:
                archinstall.log(f" {partition} (Filesystem not supported)", fg="red")

        # We then ask what to do with the partitions.
        if (option := archinstall.ask_for_disk_layout()) == "abort":
            archinstall.log(
                "Safely aborting the installation."
                "No changes to the disk or system has been made."
            )
            sys.exit(1)
        elif option == "keep-existing":
            archinstall.arguments["harddrive"].keep_partitions = True

            archinstall.log(
                " ** You will now select which partitions to use by selecting mount points (inside the installation). **"
            )
            archinstall.log(
                " ** The root would be a simple / and the boot partition /boot (as all paths are relative inside the installation). **"
            )
            mountpoints_set = []
            while True:
                # Select a partition
                # If we provide keys as options, it's better to convert them to list and sort before passing
                mountpoints_list = sorted(list(partition_mountpoints.keys()))
                partition = archinstall.generic_select(
                    mountpoints_list,
                    "Select a partition by number that you want to set a mount-point for (leave blank when done): ",
                )
                if not partition:
                    if set(mountpoints_set) & {"/", "/boot"} == {"/", "/boot"}:
                        break

                    continue

                # Select a mount-point
                mountpoint = input(f"Enter a mount-point for {partition}: ").strip(" ")
                if len(mountpoint):
                    new_filesystem = ""
                    # Get a valid & supported filesystem for the partition:
                    while 1:
                        new_filesystem = input(
                            f"Enter a valid filesystem for {partition}"
                            " and - if you don't want to format it "
                            f"(leave blank for {partition.filesystem}): "
                        ).strip(" ")
                        if len(new_filesystem) <= 0:
                            break
                        if (new_filesystem) == "-":
                            break

                        # Since the potentially new filesystem is new
                        # we have to check if we support it. We can do this by formatting /dev/null with the partitions filesystem.
                        # There's a nice wrapper for this on the partition object itself that supports a path-override during .format()
                        try:
                            partition.format(
                                new_filesystem,
                                path="/dev/null",
                                log_formatting=False,
                                allow_formatting=True,
                            )
                        except archinstall.UnknownFilesystemFormat:
                            archinstall.log(
                                f"Selected filesystem is not supported yet. If you want archinstall to support '{new_filesystem}',"
                            )
                            archinstall.log(
                                "please create a issue-ticket suggesting it on github at https://github.com/archlinux/archinstall/issues."
                            )
                            archinstall.log(
                                "Until then, please enter another supported filesystem."
                            )
                            continue
                        except archinstall.SysCallError:
                            pass  # Expected exception since mkfs.<format> can not format /dev/null. But that means our .format() function supported it.
                        break

                    # When we've selected all three criteria,
                    # We can safely mark the partition for formatting and where to mount it.
                    # TODO: allow_formatting might be redundant since target_mountpoint should only be
                    #       set if we actually want to format it anyway.
                    mountpoints_set.append(mountpoint)
                    if new_filesystem == "-":
                        partition.allow_formatting = False
                    else:
                        partition.allow_formatting = True
                    partition.target_mountpoint = mountpoint
                    # Only overwrite the filesystem definition if we selected one:
                    if len(new_filesystem) and new_filesystem != "-":
                        partition.filesystem = new_filesystem

            archinstall.log("Using existing partition table reported above.")
        elif option == "format-all":
            if not archinstall.arguments.get("filesystem", None):
                archinstall.arguments[
                    "filesystem"
                ] = archinstall.ask_for_main_filesystem_format()
            archinstall.arguments["harddrive"].keep_partitions = False
    elif archinstall.arguments["harddrive"]:
        # If the drive doesn't have any partitions, safely mark the disk with keep_partitions = False
        # and ask the user for a root filesystem.
        if not archinstall.arguments.get("filesystem", None):
            archinstall.arguments[
                "filesystem"
            ] = archinstall.ask_for_main_filesystem_format()
        archinstall.arguments["harddrive"].keep_partitions = False

    archinstall.arguments["bootloader"] = "grub-install"

    # Get the hostname for the machine
    if not archinstall.arguments.get("hostname", None):
        archinstall.arguments["hostname"] = input(
            "Desired hostname for the installation: "
        ).strip(" ")

    # Ask for additional users (super-user if root pw was not set)
    archinstall.arguments["users"] = {}
    archinstall.arguments["superusers"] = {}
    if not archinstall.arguments.get("!root-password", None):
        archinstall.arguments["superusers"] = archinstall.ask_for_superuser_account(
            "Create a required super-user with sudo privileges: ", forced=True
        )

    users, superusers = archinstall.ask_for_additional_users(
        "Enter a username to create a additional user (leave blank to skip & continue): "
    )
    archinstall.arguments["users"] = users
    archinstall.arguments["superusers"] = (
        archinstall.arguments.get("superusers", {}) | superusers
    )

    # Ask for archinstall-specific profiles (such as desktop environments etc)
    if not archinstall.arguments.get("profile", None):
        archinstall.arguments["profile"] = archinstall.select_profile()
    else:
        archinstall.arguments["profile"] = Profile(
            installer=None, path=archinstall.arguments["profile"]
        )

    # Check the potentially selected profiles preparations to get early checks if some additional questions are needed.
    if (
        archinstall.arguments["profile"]
        and archinstall.arguments["profile"].has_prep_function()
    ):
        with archinstall.arguments["profile"].load_instructions(
            namespace=f"{archinstall.arguments['profile'].namespace}.py"
        ) as imported:
            if not imported._prep_function():
                archinstall.log(
                    " * Profile's preparation requirements was not fulfilled.",
                    fg="red",
                )
                exit(1)

    # Ask for preferred kernel:
    if not archinstall.arguments.get("kernels", None):
        kernels = ["linux", "linux-lts", "linux-zen", "linux-hardened"]
        archinstall.arguments["kernels"] = archinstall.select_kernel(kernels)

    # Additional packages (with some light weight error handling for invalid package names)
    print(
        "Only packages such as base, base-devel, linux, linux-firmware, efibootmgr and optional profile packages are installed."
    )
    print(
        "If you desire a web browser, such as firefox or chromium, you may specify it in the following prompt."
    )
    if len(archinstall.arguments["packages"]):
        # Verify packages that were given
        try:
            archinstall.log(
                "Verifying that additional packages exist (this might take a few seconds)"
            )
            archinstall.validate_package_list(archinstall.arguments["packages"])
        except archinstall.RequirementError as err:
            archinstall.log(err, fg="red")
            archinstall.arguments[
                "packages"
            ] = None  # Clear the packages to trigger a new input question

    # Ask or Call the helper function that asks the user to optionally configure a network.
    if not archinstall.arguments.get("nic", None):
        archinstall.log(
            "No network configuration was selected. Network is going to be unavailable until configured manually!",
            fg="yellow",
        )


def perform_installation_steps():
    print()
    print("This is your chosen configuration:")
    archinstall.log(
        "-- Guided template chosen (with below config) --", level=logging.DEBUG
    )
    user_configuration = json.dumps(
        archinstall.arguments, indent=4, sort_keys=True, cls=archinstall.JSON
    )
    archinstall.log(user_configuration, level=logging.INFO)
    with open("/var/log/archinstall/user_configuration.json", "w") as config_file:
        config_file.write(user_configuration)
    print()

    if archinstall.arguments.get("dry_run"):
        sys.exit(0)

    if not archinstall.arguments.get("silent"):
        input("Press Enter to continue.")

    """
    Issue a final warning before we continue with something un-revertable.
    We mention the drive one last time, and count from 5 to 0.
    """

    if archinstall.arguments.get("harddrive", None):
        print(f" ! Formatting {archinstall.arguments['harddrive']} in ", end="")
        archinstall.do_countdown()

        """
        Setup the blockdevice, filesystem (and optionally encryption).
        Once that's done, we'll hand over to perform_installation()
        """
        mode = archinstall.GPT
        if archinstall.has_uefi() is False:
            mode = archinstall.MBR
        with archinstall.Filesystem(archinstall.arguments["harddrive"], mode) as fs:
            # Wipe the entire drive if the disk flag `keep_partitions`is False.
            if archinstall.arguments["harddrive"].keep_partitions is False:
                fs.use_entire_disk(
                    root_filesystem_type=archinstall.arguments.get(
                        "filesystem", "btrfs"
                    )
                )

            # Check if encryption is desired and mark the root partition as encrypted.
            if archinstall.arguments.get("!encryption-password", None):
                root_partition = fs.find_partition("/")
                root_partition.encrypted = True

            # After the disk is ready, iterate the partitions and check
            # which ones are safe to format, and format those.
            for partition in archinstall.arguments["harddrive"]:
                if partition.safe_to_format():
                    # Partition might be marked as encrypted due to the filesystem type crypt_LUKS
                    # But we might have omitted the encryption password question to skip encryption.
                    # In which case partition.encrypted will be true, but passwd will be false.
                    if partition.encrypted and (
                        passwd := archinstall.arguments.get(
                            "!encryption-password", None
                        )
                    ):
                        partition.encrypt(password=passwd)
                    else:
                        partition.format()
                else:
                    archinstall.log(
                        f"Did not format {partition} because .safe_to_format() returned False or .allow_formatting was False.",
                        level=logging.DEBUG,
                    )

            if archinstall.arguments.get("!encryption-password", None):
                # First encrypt and unlock, then format the desired partition inside the encrypted part.
                # archinstall.luks2() encrypts the partition when entering the with context manager, and
                # unlocks the drive so that it can be used as a normal block-device within archinstall.
                with archinstall.luks2(
                    fs.find_partition("/"),
                    "luksloop",
                    archinstall.arguments.get("!encryption-password", None),
                ) as unlocked_device:
                    unlocked_device.format(fs.find_partition("/").filesystem)
                    unlocked_device.mount(
                        archinstall.storage.get("MOUNT_POINT", "/mnt")
                    )
            else:
                fs.find_partition("/").mount(
                    archinstall.storage.get("MOUNT_POINT", "/mnt")
                )

            if archinstall.has_uefi():
                fs.find_partition("/boot").mount(
                    archinstall.storage.get("MOUNT_POINT", "/mnt") + "/boot"
                )

    perform_installation(archinstall.storage.get("MOUNT_POINT", "/mnt"))


def perform_installation(mountpoint):
    """
    Performs the installation steps on a block device.
    Only requirement is that the block devices are
    formatted and setup prior to entering this function.
    """
    with archinstall.Installer(
        mountpoint, kernels=archinstall.arguments.get("kernels", "linux")
    ) as installation:
        # if len(mirrors):
        # Certain services might be running that affects the system during installation.
        # Currently, only one such service is "reflector.service" which updates /etc/pacman.d/mirrorlist
        # We need to wait for it before we continue since we opted in to use a custom mirror/region.
        installation.log(
            "Waiting for automatic mirror selection (reflector) to complete.",
            level=logging.INFO,
        )
        while archinstall.service_state("reflector") not in ("dead", "failed"):
            time.sleep(1)
        # Set mirrors used by pacstrap (outside of installation)
        if archinstall.arguments.get("mirror-region", None):
            archinstall.use_mirrors(
                archinstall.arguments["mirror-region"]
            )  # Set the mirrors for the live medium
        if installation.minimal_installation():
            installation.set_locale(
                archinstall.arguments["sys-language"],
                archinstall.arguments["sys-encoding"].upper(),
            )
            installation.set_hostname(archinstall.arguments["hostname"])
            if archinstall.arguments["mirror-region"].get("mirrors", None) is not None:
                installation.set_mirrors(
                    archinstall.arguments["mirror-region"]
                )  # Set the mirrors in the installation medium
            if (
                archinstall.arguments["bootloader"] == "grub-install"
                and archinstall.has_uefi()
            ):
                installation.add_additional_packages("grub")
            installation.add_bootloader(archinstall.arguments["bootloader"])

            # If user selected to copy the current ISO network configuration
            # Perform a copy of the config
            if (
                archinstall.arguments.get("nic", {})
                == "Copy ISO network configuration to installation"
            ):
                installation.copy_iso_network_config(
                    enable_services=True
                )  # Sources the ISO network configuration to the install medium.
            elif archinstall.arguments.get("nic", {}).get("NetworkManager", False):
                installation.add_additional_packages("networkmanager")
                installation.enable_service("NetworkManager.service")
                # Otherwise, if a interface was selected, configure that interface
            elif archinstall.arguments.get("nic", {}):
                installation.configure_nic(**archinstall.arguments.get("nic", {}))
                installation.enable_service("systemd-networkd")
                installation.enable_service("systemd-resolved")

            if archinstall.arguments.get("audio", None) is not None:
                installation.log(
                    f"This audio server will be used: {archinstall.arguments.get('audio', None)}",
                    level=logging.INFO,
                )
                if archinstall.arguments.get("audio", None) == "pipewire":
                    print("Installing pipewire ...")

                    installation.add_additional_packages(
                        [
                            "pipewire",
                            "pipewire-alsa",
                            "pipewire-jack",
                            "pipewire-media-session",
                            "pipewire-pulse",
                            "gst-plugin-pipewire",
                            "libpulse",
                        ]
                    )
                elif archinstall.arguments.get("audio", None) == "pulseaudio":
                    print("Installing pulseaudio ...")
                    installation.add_additional_packages("pulseaudio")
            else:
                installation.log(
                    "No audio server will be installed.", level=logging.INFO
                )

            if (
                len(archinstall.arguments.get("packages", [])) != 0
                and archinstall.arguments.get("packages", [])[0] != ""
            ):
                installation.add_additional_packages(
                    archinstall.arguments.get("packages", None)
                )

            if archinstall.arguments.get("profile", None):
                installation.install_profile(archinstall.arguments.get("profile", None))

            for user, user_info in archinstall.arguments.get("users", {}).items():
                installation.user_create(user, user_info["!password"], sudo=False)

            for superuser, user_info in archinstall.arguments.get(
                "superusers", {}
            ).items():
                installation.user_create(superuser, user_info["!password"], sudo=True)

            if timezone := archinstall.arguments.get("timezone", None):
                installation.set_timezone(timezone)

            if archinstall.arguments.get("ntp", False):
                installation.activate_ntp()

            if (root_pw := archinstall.arguments.get("!root-password", None)) and len(
                root_pw
            ):
                installation.user_set_pw("root", root_pw)

            # This step must be after profile installs to allow profiles to install language pre-requisits.
            # After which, this step will set the language both for console and x11 if x11 was installed for instance.
            installation.set_keyboard_language(
                archinstall.arguments["keyboard-language"]
            )

            if (
                archinstall.arguments["profile"]
                and archinstall.arguments["profile"].has_post_install()
            ):
                with archinstall.arguments["profile"].load_instructions(
                    namespace=f"{archinstall.arguments['profile'].namespace}.py"
                ) as imported:
                    if not imported._post_install():
                        archinstall.log(
                            " * Profile's post configuration requirements was not fulfilled.",
                            fg="red",
                        )
                        sys.exit(1)

        # If the user provided a list of services to be enabled, pass the list to the enable_service function.
        # Note that while it's called enable_service, it can actually take a list of services and iterate it.
        if archinstall.arguments.get("services", None):
            installation.enable_service(*archinstall.arguments["services"])

        # If the user provided custom commands to be run post-installation, execute them now.
        if archinstall.arguments.get("custom-commands", None):
            run_custom_user_commands(
                archinstall.arguments["custom-commands"], installation
            )

        installation.log(
            "For post-installation tips, see https://wiki.archlinux.org/index.php/Installation_guide#Post-installation",
            fg="yellow",
        )
        try:
            installation.drop_to_shell()
        except:
            pass

    # For support reasons, we'll log the disk layout post installation (crash or no crash)
    archinstall.log(
        f"Disk states after installing: {archinstall.disk_layouts()}",
        level=logging.DEBUG,
    )


if not check_mirror_reachable():
    archinstall.log(
        "Arch Linux mirrors are not reachable" "Please check your internet connection",
        fg="red",
    )
    sys.exit(1)

defaults()

ask_user_questions()

perform_installation_steps()
