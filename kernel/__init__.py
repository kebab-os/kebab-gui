import os
import shutil
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Clean up __pycache__
pycache_path = os.path.join(os.path.dirname(__file__), '__pycache__')
if os.path.exists(pycache_path):
    shutil.rmtree(pycache_path)

# Create temporary directory
temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temporary')
os.makedirs(temp_dir, exist_ok=True)

# Move web_temp.png to temporary directory if it appears
web_temp_path = 'web_temp.png'
if os.path.exists(web_temp_path):
    shutil.move(web_temp_path, os.path.join(temp_dir, 'web_temp.png'))
