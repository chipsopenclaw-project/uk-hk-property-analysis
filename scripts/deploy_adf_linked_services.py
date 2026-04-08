# deploy_adf_linked_services.py
# Deploys ADF Linked Services from JSON files in adf/linked_services/

import json
import subprocess
import sys
import os
import glob

FACTORY_NAME = "adf-ukhkprop-dev"
RESOURCE_GROUP = "rg-ukhkprop-dev"

def deploy_linked_service(file_path):
    with open(file_path) as f:
        d = json.load(f)

    ls_name = d["name"]
    props = json.dumps(d["properties"])

    print(f"Deploying linked service: {ls_name}")

    result = subprocess.run([
        "az", "datafactory", "linked-service", "create",
        "--factory-name", FACTORY_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--name", ls_name,
        "--properties", props
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(result.returncode)

    print(f"Successfully deployed: {ls_name}")

if __name__ == "__main__":
    files = glob.glob("adf/linked_services/*.json")
    if not files:
        print("No linked service files found")
        sys.exit(0)

    for file_path in files:
        deploy_linked_service(file_path)

    print("All linked services deployed!")
