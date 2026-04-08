# deploy_adf_datasets.py
# Deploys ADF Datasets from JSON files in adf/datasets/

import json
import subprocess
import sys
import glob

FACTORY_NAME   = "adf-ukhkprop-dev"
RESOURCE_GROUP = "rg-ukhkprop-dev"

def deploy_dataset(file_path):
    with open(file_path) as f:
        d = json.load(f)

    ds_name = d["name"]
    props   = json.dumps(d["properties"])

    print(f"Deploying dataset: {ds_name}")

    result = subprocess.run([
        "az", "datafactory", "dataset", "create",
        "--factory-name", FACTORY_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--name", ds_name,
        "--properties", props
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(result.returncode)

    print(f"Successfully deployed: {ds_name}")

if __name__ == "__main__":
    files = glob.glob("adf/datasets/*.json")
    if not files:
        print("No dataset files found")
        sys.exit(0)

    for file_path in files:
        deploy_dataset(file_path)

    print("All datasets deployed!")
