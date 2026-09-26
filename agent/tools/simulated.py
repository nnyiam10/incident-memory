import json
from pathlib import Path

ROOT = Path(__file__).parents[2] / "sandbox" / "incidents"

def load_scenario(name: str) -> dict:
    with open(ROOT / name / "scenario.json") as handle:
        return json.load(handle)

def search_logs(name: str, contains: str = "") -> list[str]:
    logs = load_scenario(name)["logs"]
    return [line for line in logs if contains.lower() in line.lower()]

def get_deployments(name: str) -> list[dict]:
    return load_scenario(name)["deployments"]

def query_metrics(name: str) -> dict:
    return load_scenario(name)["metrics"]

