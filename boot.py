# kebab-gui v1.1.3
# ---------------------------------
#
# Welcome to kebab-gui! Please read the README to to make sure that
# you have all the dependencies intalled and know how to use it.

from kernel.core import boot
import argparse

print("Booting kebab-gui...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Boot kebab-gui")
    parser.add_argument("--vm", action="store_true", help="Enable VM kiosk mode")
    args = parser.parse_args()
    boot(vm_mode=args.vm)
