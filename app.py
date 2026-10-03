"""A small web page that shows what runs in my homelab."""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import homelab

app = FastAPI(title="Homelab status")
templates = Jinja2Templates(directory="templates")


@app.get("/api/status")
def status():
    """The same data as JSON - for scripts, bots, and later the AI agent."""
    return {"hosts": homelab.get_hosts(), "datastores": homelab.get_datastores(),
            "vms": homelab.get_vms(), "containers": homelab.get_containers()}


@app.get("/")
def index(request: Request):
    """The web page."""
    data = status()
    return templates.TemplateResponse(request, "index.html", {
        "hosts": data["hosts"],
        "datastores": data["datastores"],
        "vms": data["vms"],
        "containers": data["containers"],
        "vms_on": sum(vm["on"] for vm in data["vms"]),
        "containers_running": sum(c["running"] for c in data["containers"]),
    })
