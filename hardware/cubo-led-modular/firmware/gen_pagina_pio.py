Import("env")
import subprocess, sys
subprocess.run([sys.executable, "gen_pagina.py"], check=True)
