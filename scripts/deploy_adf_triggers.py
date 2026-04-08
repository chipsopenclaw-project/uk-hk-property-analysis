# deploy_adf_triggers.py
# Deploys ADF Triggers from JSON files in adf/triggers/

import json
import subprocess
import sys
import glob

FACTORY_NAME   = "adf-ukhkprop-dev"
RESOURCE_GROUP = "rg-ukhkprop-dev"

def deploy_trigger(file_path):
    with open(file_path) as f:
        d = json.load(f)

    trigger_name = d["name"]
    props = json.dumps(d["properties"])

    print(f"Deploying trigger: {trigger_name}")

    # First stop trigger if exists
    subprocess.run([
        "az", "datafactory", "trigger", "stop",
        "--factory-name", FACTORY_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--name", trigger_name
    ], capture_output=True, text=True)

    # Create/update trigger
    result = subprocess.run([
        "az", "datafactory", "trigger", "create",
        "--factory-name", FACTORY_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--name", trigger_name,
        "--properties", props
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(result.returncode)

    # Start trigger
    result = subprocess.run([
        "az", "datafactory", "trigger", "start",
        "--factory-name", FACTORY_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--name", trigger_name
    ], capture_output=True, text=True)

    print(f"Successfully deployed and started: {trigger_name}")

if __name__ == "__main__":
    files = glob.glob("adf/triggers/*.json")
    if not files:
        print("No trigger files found")
        sys.exit(0)

    for file_path in files:
        deploy_trigger(file_path)

    print("All triggers deployed!")
