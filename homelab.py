import requests

PROMETHEUS = "http://192.168.0.10:9090"


def query(promql):
    response = requests.get(f"{PROMETHEUS}/api/v1/query", params={"query": promql})
    response.raise_for_status()
    return response.json()["data"]["result"]
def get_vms():
    vms = []
    for item in query("vmware_vm_power_state"):
         name = item["metric"]["vm_name"]
         is_on = item["value"][1] == "1"
         vms.append({"name": name, "on": is_on})
    return vms
