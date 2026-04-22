#!/usr/bin/env sh
set -eu

# Build a bootable Alpine ISO that launches kebab-gui.
# Run this as root on Alpine Linux.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="kebabos-live"
ARCH="x86_64"
ALPINE_BRANCH="${ALPINE_BRANCH:-v3.21}"
ALPINE_TAG="${ALPINE_TAG:-${ALPINE_BRANCH}}"

if ! command -v apk >/dev/null 2>&1; then
  echo "This builder is Alpine-specific. Run it on Alpine Linux." >&2
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root on the Alpine build VM" >&2
  exit 1
fi

echo "Installing Alpine ISO build dependencies..."
apk add --no-cache \
  abuild alpine-conf apk-tools busybox fakeroot syslinux xorriso squashfs-tools grub mtools \
  git rsync openssl

BUILD_USER="${BUILD_USER:-kebabbuild}"
if ! id "$BUILD_USER" >/dev/null 2>&1; then
  adduser -D -s /bin/sh "$BUILD_USER"
fi

BUILD_HOME="$(getent passwd "$BUILD_USER" | cut -d: -f6)"
BUILD_ROOT="${BUILD_HOME}/.build/alpine-iso"
OUT_DIR="${BUILD_ROOT}/out"
WORK_DIR="${BUILD_ROOT}/work"
APORTS_DIR="${BUILD_ROOT}/aports"
MKHOME="${BUILD_ROOT}/home"
PLUGIN_DIR="${MKHOME}/.mkimage"
PAYLOAD_DIR="${PLUGIN_DIR}/payload"

if ! ls /etc/apk/keys/*.rsa.pub >/dev/null 2>&1; then
  echo "Generating abuild signing key..."
fi

mkdir -p "$BUILD_HOME/.abuild"
PACKAGER_PRIVKEY="$BUILD_HOME/.abuild/kebabbuild.rsa"
PACKAGER_PUBKEY="$PACKAGER_PRIVKEY.pub"
if [ ! -f "$PACKAGER_PRIVKEY" ] || [ ! -f "$PACKAGER_PUBKEY" ]; then
  openssl genrsa -out "$PACKAGER_PRIVKEY" 4096 >/dev/null 2>&1
  openssl rsa -in "$PACKAGER_PRIVKEY" -pubout -out "$PACKAGER_PUBKEY" >/dev/null 2>&1
fi
cat > "$BUILD_HOME/.abuild/abuild.conf" <<EOF
PACKAGER_PRIVKEY="$PACKAGER_PRIVKEY"
EOF
chmod 600 "$PACKAGER_PRIVKEY" "$PACKAGER_PUBKEY"
chown -R "$BUILD_USER:$BUILD_USER" "$BUILD_HOME/.abuild"

echo "Preparing build workspace..."
rm -rf "$BUILD_ROOT"
mkdir -p "$OUT_DIR" "$WORK_DIR" "$PLUGIN_DIR" "$PAYLOAD_DIR"
chown -R "$BUILD_USER:$BUILD_USER" "$BUILD_ROOT"

if [ ! -d "$APORTS_DIR/.git" ]; then
  git clone --depth=1 https://gitlab.alpinelinux.org/alpine/aports.git "$APORTS_DIR"
fi

echo "Copying project payload into build context..."
rsync -a \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.build' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$ROOT_DIR/" "$PAYLOAD_DIR/kebab-gui/"

cat > "$PLUGIN_DIR/mkimg.kebab.sh" <<'EOF'
profile_kebab() {
  profile_standard
  title="kebabOS Live (Alpine)"
  desc="Alpine appliance image for kebab-gui"
  image_name="kebabos-live"

  apks="$apks \
    alpine-base openrc eudev \
    python3 py3-pip py3-virtualenv py3-pygame py3-requests \
    xorg-server xinit openbox xterm xsetroot xf86-video-vesa xf86-input-libinput mesa-dri-gallium \
    chromium xclip git bash ca-certificates"

  apkovl="genapkovl-kebab.sh"
}
EOF

cat > "$PLUGIN_DIR/genapkovl-kebab.sh" <<'EOF'
#!/bin/sh
set -eu

tmp="$1"
script_dir="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
payload_dir="$script_dir/payload/kebab-gui"

mkdir -p "$tmp/opt"
cp -a "$payload_dir" "$tmp/opt/kebab-gui"

mkdir -p "$tmp/usr/local/bin"
cat > "$tmp/usr/local/bin/kebab-gui-vm" <<'LAUNCHER'
#!/bin/sh
set -eu

cd /opt/kebab-gui

if [ ! -x .venv/bin/python3 ]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install pygame requests html2image || true
fi

if [ -x .venv/bin/python3 ]; then
  exec .venv/bin/python3 boot.py --vm
fi

exec python3 boot.py --vm
LAUNCHER
chmod +x "$tmp/usr/local/bin/kebab-gui-vm"

cat > "$tmp/usr/local/bin/kebab-session" <<'SESSION'
#!/bin/sh
set -eu
openbox &
exec /usr/local/bin/kebab-gui-vm
SESSION
chmod +x "$tmp/usr/local/bin/kebab-session"

mkdir -p "$tmp/etc/profile.d"
cat > "$tmp/etc/profile.d/kebab-autostart.sh" <<'PROFILE'
#!/bin/sh
if [ -z "${DISPLAY:-}" ] && [ "$(tty 2>/dev/null || true)" = "/dev/tty1" ]; then
  exec startx /usr/local/bin/kebab-session -- :0 vt1
fi
PROFILE
chmod +x "$tmp/etc/profile.d/kebab-autostart.sh"

mkdir -p "$tmp/etc"
if [ -f "$tmp/etc/inittab" ]; then
  sed -i 's#tty1::respawn:/sbin/getty 38400 tty1#tty1::respawn:/sbin/getty -n -l /bin/sh 38400 tty1#' "$tmp/etc/inittab" || true
else
  cat > "$tmp/etc/inittab" <<'INITTAB'
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown

tty1::respawn:/sbin/getty -n -l /bin/sh 38400 tty1
tty2::respawn:/sbin/getty 38400 tty2
tty3::respawn:/sbin/getty 38400 tty3
tty4::respawn:/sbin/getty 38400 tty4
INITTAB
fi

settings_file="$tmp/opt/kebab-gui/.config/settings.ini"
if [ -f "$settings_file" ]; then
  sed -i 's/^enabled\s*=.*/enabled = true/' "$settings_file" || true
  sed -i 's/^auto_login\s*=.*/auto_login = true/' "$settings_file" || true
  sed -i 's/^auto_login_user\s*=.*/auto_login_user = admin/' "$settings_file" || true
fi

chown -R 0:0 "$tmp/opt/kebab-gui"
EOF
chmod +x "$PLUGIN_DIR/genapkovl-kebab.sh"

REPO_MAIN="https://dl-cdn.alpinelinux.org/alpine/${ALPINE_BRANCH}/main"
REPO_COMMUNITY="https://dl-cdn.alpinelinux.org/alpine/${ALPINE_BRANCH}/community"

echo "Building Alpine ISO (this can take several minutes)..."
chown -R "$BUILD_USER:$BUILD_USER" "$BUILD_ROOT"
su -s /bin/sh "$BUILD_USER" -c "PACKAGER_PRIVKEY='$PACKAGER_PRIVKEY' PACKAGER_PUBKEY='$PACKAGER_PUBKEY' HOME='$MKHOME' sh '$APORTS_DIR/scripts/mkimage.sh' \
  --tag '$ALPINE_TAG' \
  --outdir '$OUT_DIR' \
  --workdir '$WORK_DIR' \
  --arch '$ARCH' \
  --profile kebab \
  --hostkeys \
  --repository '$REPO_MAIN' \
  --repository '$REPO_COMMUNITY'"

ISO_PATH="$(ls -1t "$OUT_DIR"/*.iso 2>/dev/null | head -n 1 || true)"
if [ -n "$ISO_PATH" ] && [ -f "$ISO_PATH" ]; then
  OUT_PATH="${ROOT_DIR}/${IMAGE_NAME}.iso"
  cp "$ISO_PATH" "$OUT_PATH"
  echo ""
  echo "Bootable Alpine image created: $OUT_PATH"
  echo "Attach this ISO as optical media in a VirtualBox VM and boot."
else
  echo "ISO build finished but no .iso file was found in $OUT_DIR" >&2
  exit 1
fi
