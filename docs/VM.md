## VM Mode (Kiosk)

This project is still an application (not a standalone kernel), but you can run it in a VM like an operating-system shell by auto-starting it fullscreen.

### 1) Enable VM settings

Edit [.config/settings.ini](../.config/settings.ini):

```ini
[vm]
enabled = true
auto_login = true
auto_login_user = admin
```

### 2) Prepare a Linux VM guest

From the repository root:

```bash
bash install/vm-linux.sh
```

This creates:
- `~/.local/bin/kebab-gui-vm` launcher
- `~/.config/autostart/kebab-gui.desktop` autostart entry
- project `.venv` with dependencies

### 3) Enable desktop auto-login in your VM

Set your VM user to auto-login in your distro display manager (GDM, SDDM, LightDM, etc).

### 4) Reboot VM

On login, kebab-gui starts fullscreen automatically.

## Manual Run

You can always start VM mode manually:

```bash
python boot.py --vm
```

## Notes

- This provides an OS-like kiosk experience inside a VM.
- It does not generate a bootable ISO or replace the guest OS kernel.
- User data is isolated per login user under `storage/users/<username>/`.

## No-Desktop Kiosk Option (Closer to "Booting Into kebab-gui")

If you do not want a desktop autostart entry, you can run kebab-gui directly from TTY login.

1) Keep VM mode enabled in `.config/settings.ini`.
2) Install dependencies and launcher with `bash install/vm-linux.sh`.
3) Enable text-console autologin for `tty1` in your guest Linux.
4) Add this to the VM user's `~/.bash_profile`:

```bash
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
	exec "$HOME/.local/bin/kebab-gui-vm"
fi
```

After reboot, the VM logs into `tty1` and launches kebab-gui immediately, without starting a desktop session first.

If you want a bootable ISO image instead of configuring an existing VM guest, follow [Bootable Image](Bootable_Image.md).
