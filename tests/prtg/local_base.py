from enum import Enum

import cores
import sensor
import device
import requests
import terminal_outputs
import typer
import config
import channel
from rich import print


# TODO: install the autocomplete for the app
app = typer.Typer(no_args_is_help=True, help="PRTG administration tool")
app.add_typer(cores.app, name="cores", help="Information about PRTG Cores ")
app.add_typer(config.app, name="config", help="Interact with app config")
app.add_typer(sensor.app, name="sensor", help="Interact with sensors in PRTG")
app.add_typer(device.app, name="device", help="Interact with devices in PRTG")
app.add_typer(channel.app, name="channel", help="Interact with sensor channels in PRTG")

cores = Enum(
    "cores",
    [
        "networkdc",
        "networkremote-1",
        "serveronprem",
        "networkremote-2",
        "serveresx",
        "serverazure",
        "nttdevices",
    ],
)

Actions = {
    "get_prop": "getobjectproperty.htm",
    "set_prop": "setobjectproperty.htm",
    "duplicate": "duplicateobject.htm",
    "pause": "pause.htm",
    "resume": "resume.htm",
}

exclude = ["Probe Device", "Cluster Probe Device", "PRTG Core Server", ""]


def base_url(core: str, action: str = None) -> str:
    url = f"https://{core}.agency.ok.local/api/"

    match action:
        case "get_prop":
            url = url + Actions["get_prop"]
        case "set_prop":
            url = url + Actions["set_prop"]
        case "duplicate":
            url = url + Actions["duplicate"]
        case "pause":
            url = url + Actions["pasue"]
        case "resume":
            url = url + Actions["resume"]
        # case None:
        # TODO: come back and check if you need a none testcase
        case _:
            print("Action Not found, valid query options are: ")
            for key in Actions.keys():
                print(key)
            raise typer.Exit(code=126)
    return url


def query_url(core: str) -> str:
    return f"https://{core}.agency.ok.local/api/table.json"


def PRTG_Get_request(url: str, params: dict = None):

    res = requests.get(url, params=params)
    try:
        return res.json()
    except requests.JSONDecodeError:
        if res.status_code == 200:
            print("[green]Response is not in JSON format, but 200 code returned")
        elif res.status_code == 400:
            print(f"[bold red] Response Code:{res.status_code}, Check input parameters")

        return res.text


def Get_All_PRTG_Hostnames() -> list:
    network_server_hostnames = []
    server_cores = [
        cores.serverazure.name,
        cores.serveresx.name,
        cores.serveronprem.name,
    ]
    for core in server_cores:
        network_server_hostnames = [
            *network_server_hostnames,
            *Get_Core_Hostnames(core),
        ]
    return network_server_hostnames


def Get_Core_Hostnames(core: str) -> list:
    query_url = f"https://{core}.agency.ok.local/api/table.json?content=devices&output=json&columns=objid,name,host,probe"
    devices = PRTG_Get_request(query_url)["devices"]
    return [device["name"] for device in devices]


def Get_Sensor_Status(sensor_type: str, core: str):
    query_url = f"https://{core}.agency.ok.local/api/table.json?content=sensors&output=json&columns=objid,group,device,sensor,status,message&filter_status=5&filter_sensor={sensor_type}"
    sensors = PRTG_Get_request(query_url)["sensors"]
    terminal_outputs.create_sensor_status_table(sensors)
