import os
import subprocess
import sys

# Get the port from the environment variable
port = os.environ.get("PORT", "8080")

# Use subprocess to run the Streamlit command
cmd = [
    f"{sys.executable}",
    "-m",
    "streamlit",
    "run",
    "0_🏠_Home.py",
    "--server.port",
    port,
    "--server.address",
    "0.0.0.0",
]

subprocess.call(cmd)