"""Exercise the installed distribution without importing the source checkout."""
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMMAND = 'openapi-sentinel'
MODULE = 'openapi_sentinel'

def main():
    executable = Path(sysconfig.get_path("scripts")) / (COMMAND + (".exe" if os.name == "nt" else ""))
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run([str(executable), "--help"], cwd=directory, env=environment, check=True)
        subprocess.run([sys.executable, "-I", "-m", MODULE, "--help"], cwd=directory, env=environment, check=True)
        subprocess.run([str(executable), 'lint', str(ROOT / 'fixtures/offer-api.json')], cwd=directory, env=environment, check=True)
    print("Installed distribution smoke check passed:", importlib.metadata.version('openapi-sentinel'))

if __name__ == "__main__":
    main()
