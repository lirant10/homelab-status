import json
import os
import sys

from ollama import Client

import homelab

MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
client = Client(host=os.environ.get("OLLAMA_URL", "http://localhost:11434"))

SYSTEM_PROMPT = (
    "You are a homelab assistant. Use the tools to get live data about "
    "VMs and containers before you answer. Keep answers short."
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


TOOLS = {"get_vms": get_vms, "get_containers": get_containers}


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
