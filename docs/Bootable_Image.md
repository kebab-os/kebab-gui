## Bootable OS Image (VirtualBox)

This project can now be packaged into a bootable Linux ISO that auto-logs in and launches kebab-gui.

Important: this image is still Linux-based (not a custom kernel rewrite). It boots as a dedicated kebab-gui appliance.

### Build Requirements (Host Machine)

Use an Alpine Linux host (or Alpine VM) with sudo.

### 1) Build the ISO

From repository root:

```bash
chmod +x install/build-bootable-iso.sh
bash install/build-bootable-iso.sh
```

Output:

- `kebabos-live.iso` in the repository root.

### 2) Create VirtualBox VM

- Type: Linux
- Version: Other Linux (64-bit)
- RAM: 4096 MB (minimum 2048 MB)
- CPUs: 2
- Video memory: 128 MB
- Graphics controller: VMSVGA
- Enable 3D acceleration

Attach `kebabos-live.iso` as optical media and boot.

### 3) First Boot Behavior

- Alpine boots from the generated ISO.
- The image includes a startup profile that launches X/Openbox on `tty1`.
- `kebab-gui` auto-launches via `/usr/local/bin/kebab-gui-vm`.

### Notes

- Browser rendering uses `html2image` + Chromium inside the image.
- Project source is bundled under `/opt/kebab-gui` in the live system.
- Build time can be long depending on host network and CPU speed.
- The builder uses Alpine `mkimage.sh` from `aports` and creates a real bootable ISO.
