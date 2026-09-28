import json
import os
import sys

from ollama import Client

import homelab

MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
client = Client(host=os.environ.get("OLLAMA_URL", "http://localhost:11434"), timeout=120)

SYSTEM_PROMPT = (
    "You are a homelab assistant. Use the tools to get live data about "
    "VMs and containers before you answer. When you report containers, also "
    "check get_down_targets: containers on a host whose exporter is down are "
    "missing from the data, so never say all containers are running without "
    "mentioning down targets. Keep answers short. Plain text only, no Markdown."
)


def get_vms() -> str:
    """Get all VMs on the ESXi host and whether each one is powered on.

    Returns:
        JSON list of VMs, each with name and on (true or false)
    """
    return json.dumps(homelab.get_vms())


def get_containers() -> str:
    """Get all Podman containers in the lab with their host, image and state.

    Returns:
        JSON list of containers, each with name, host, image, state and running
    """
    return json.dumps(homelab.get_containers())


def get_down_targets() -> str:
    """Get monitoring targets that Prometheus cannot reach right now.

    Returns:
        JSON list of down targets, each with job and instance
    """
    return json.dumps(homelab.get_down_targets())


TOOLS = {
    "get_vms": get_vms,
    "get_containers": get_containers,
    "get_down_targets": get_down_targets,
}


def ask(question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    # Safety limit: stop after 5 rounds so a confused model can't loop forever
    for _ in range(5):
        response = client.chat(
            model=MODEL, messages=messages, tools=list(TOOLS.values()), think=False
        )
        messages.append(response.message)
        # No tool calls means the model is done and wrote its final answer
        if not response.message.tool_calls:
            return response.message.content
        for call in response.message.tool_calls:
            name = call.function.name
            print(f"[tool] {name}")
            if name in TOOLS:
                result = TOOLS[name]()
            else:
                result = f"Unknown tool: {name}"
            messages.append({"role": "tool", "content": result, "tool_name": name})
    return "Stopped: too many tool rounds."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is off in the lab?"
    print(ask(question))
