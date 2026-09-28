import os
import requests

PROMETHEUS = os.environ["PROMETHEUS_URL"]

CONTAINER_STATES = {"0": "created", "1": "initialized", "2": "running", "3": "stopped",
                    "4": "paused", "5": "exited", "6": "removing", "7": "stopping"}

CONTAINERS_QUERY = ("max by (instance, name, image) (podman_container_state "
                    "* on(instance, id) group_left(name, image) podman_container_info)")


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


def get_containers():
    containers = []
    for item in query(CONTAINERS_QUERY):
        m = item["metric"]
        state = CONTAINER_STATES.get(item["value"][1], "unknown")
        containers.append({"name": m["name"], "host": m["instance"], "image": m["image"],
                           "state": state, "running": state == "running"})
    return containers


def get_down_targets():
    targets = []
    for item in query("up == 0"):
        m = item["metric"]
        targets.append({"job": m.get("job", ""), "instance": m.get("instance", "")})
    return targets
