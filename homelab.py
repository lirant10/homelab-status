import os
import requests

PROMETHEUS = os.environ["PROMETHEUS_URL"]

CONTAINER_STATES = {"0": "created", "1": "initialized", "2": "running", "3": "stopped",
                    "4": "paused", "5": "exited", "6": "removing", "7": "stopping"}

CONTAINERS_QUERY = ("max by (instance, name, image) (podman_container_state "
                    "* on(instance, id) group_left(name, image) podman_container_info)")

# max by (...) removes duplicates when the same VM or host is scraped twice
# (for example directly from ESXi and again through vCenter)
VMS_QUERY = "max by (vm_name, host_name) (vmware_vm_power_state)"
HOST_CPU_QUERY = ("max by (host_name) (vmware_host_cpu_usage) "
                  "/ max by (host_name) (vmware_host_cpu_max) * 100")
HOST_MEMORY_QUERY = ("max by (host_name) (vmware_host_memory_usage) "
                     "/ max by (host_name) (vmware_host_memory_max) * 100")
DATASTORE_QUERY = ("max by (ds_name) (1 - vmware_datastore_freespace_size "
                   "/ vmware_datastore_capacity_size) * 100")


def query(promql):
    response = requests.get(f"{PROMETHEUS}/api/v1/query", params={"query": promql})
    response.raise_for_status()
    return response.json()["data"]["result"]


def get_vms():
    vms = []
    for item in query(VMS_QUERY):
        m = item["metric"]
        is_on = item["value"][1] == "1"
        vms.append({"name": m["vm_name"], "host": m.get("host_name", ""), "on": is_on})
    return sorted(vms, key=lambda vm: (vm["host"], vm["name"]))


def percent(value):
    return None if value is None else round(value, 1)


def get_hosts():
    """ESXi hosts with CPU % and memory % (None when the metric is missing)."""
    cpu = {i["metric"]["host_name"]: float(i["value"][1]) for i in query(HOST_CPU_QUERY)}
    memory = {i["metric"]["host_name"]: float(i["value"][1]) for i in query(HOST_MEMORY_QUERY)}
    hosts = []
    for name in sorted(cpu.keys() | memory.keys()):
        hosts.append({"name": name,
                      "cpu_percent": percent(cpu.get(name)),
                      "memory_percent": percent(memory.get(name))})
    return hosts


def get_datastores():
    """Datastores with how full they are, in %."""
    datastores = []
    for item in query(DATASTORE_QUERY):
        datastores.append({"name": item["metric"]["ds_name"],
                           "used_percent": round(float(item["value"][1]), 1)})
    return sorted(datastores, key=lambda ds: ds["name"])


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
