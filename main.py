import os
import requests

PROMETHEUS = os.environ["PROMETHEUS_URL"]


def query(promql):
    """Ask Prometheus a question and return the list of results."""
    response = requests.get(f"{PROMETHEUS}/api/v1/query", params={"query": promql})
    response.raise_for_status()
    return response.json()["data"]["result"]


print("VMs:")
for vm in query("vmware_vm_power_state"):
    name = vm["metric"]["vm_name"]
    is_on = vm["value"][1] == "1"
    print("  ", "🟢" if is_on else "🔴", name)
