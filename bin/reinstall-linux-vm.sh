# unused script

'''
#!/usr/bin/env bash
set -euo pipefail

# Run this script from the repository root on a Linux VM guest.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

mkdir -p .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pygame requests html2image

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/kebab-gui-vm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="__ROOT_DIR__"
cd "$ROOT_DIR"
source .venv/bin/activate
# Best effort: keep display awake in kiosk mode.
command -v xset >/dev/null 2>&1 && xset s off -dpms || true
python boot.py --vm
EOF
sed -i "s|__ROOT_DIR__|$ROOT_DIR|g" "$HOME/.local/bin/kebab-gui-vm"
chmod +x "$HOME/.local/bin/kebab-gui-vm"

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/kebab-gui.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=kebab-gui VM
Exec=$HOME/.local/bin/kebab-gui-vm
X-GNOME-Autostart-enabled=true
Terminal=false
EOF

echo "VM setup complete."
echo "Next steps:"
echo "1) Enable auto-login for your VM user in your display manager"
echo "2) Reboot the VM; kebab-gui should auto-start fullscreen"
'''
