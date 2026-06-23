import os

# Ensure Qt can run headless during tests.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
