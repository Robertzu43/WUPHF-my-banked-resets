"""Launch the per-user scheduled check from the installed project folder."""
import os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
from wuphf.cli import main
main(['run'])
