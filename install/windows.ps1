cd ~
if (!(Test-Path .kebab)) { mkdir .kebab }
cd .kebab
curl.exe -L https://github.com/kebab-os/kebab-gui/archive/refs/heads/main.zip -o kebab-gui.zip
Expand-Archive -Path kebab-gui.zip -DestinationPath . -Force
cd kebab-gui-main/src
pip install pygame requests html2image
