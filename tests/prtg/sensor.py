from dataclasses import dataclass, asdict
import typer
import config
import re
from rich import print
from typing import List, Optional
from typing_extensions import Annotated
import local_base
import time
import terminal_outputs as outputs
from enum import Enum

app = typer.Typer(no_args_is_help=True)


class Output(str, Enum):
    text = "text"
    table = "table"


@dataclass
class QueryParams:
    action: Optional[int] = None
    apitoken: Optional[str] = None
    columns: Optional[str] = None
    content: Optional[str] = "sensors"
    count: Optional[str] = "50000"
    filter_name: Optional[str] = None
    filter_objid: Optional[str] = None
    filter_tags: Optional[list[str]] = None
    id: Optional[str] = None
    name: Optional[str] = None
    output: Optional[str] = "json"
    targetid: Optional[int] = None


# TODO: Implement a way to accept several name types. For now we only accept 1 sensor ID


@app.command(no_args_is_help=True)
def duplicate(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    sensor_name: Annotated[
        str, typer.Argument(help="User given name that will applied")
    ],
    source_sensor: Annotated[
        str, typer.Option(help="ID of the sensor to be duplicated")
    ] = None,
    target_device: Annotated[
        str, typer.Option(help="IDs of the device needing the sensor")
    ] = None,
) -> None:
    """
    Copy a sensor type from one device to one or multiple devices.


    Copy sensor to single device:  prtg sensor duplicate serveronprem Ping --source_sensor 35921 --target device 52345.

    Copy sensor to multiple devices: prtg sensor duplicate serveronprem Ping --source_sensor 35921 --target device '52345 7231 56790 34219'.
    """

    token = config.get_token(core)

    expression = re.compile(r"sensor\.htm\?id=(?P<sensor_id>\d+)")
    target_device = target_device.split()
    source_sensor = source_sensor.split()

    for target_ID in target_device:
        print(f"Sensors being Applied to Device: {target_ID}")
        print("===================START=====================")

        for sensor_id in source_sensor:
            if has_sensor(core, target_ID, token=token, sensor_name=sensor_name):
                print(f"Sensor:{sensor_name}, Already applied to device:{target_ID}")
                print("Remove sensor nor change sensor name before applying duplicate")
                continue

            print(f"Applying {sensor_name} sensor")

            url = local_base.base_url(core, action="duplicate")
            url_params = QueryParams(
                id=sensor_id, name=sensor_name, targetid=target_ID, apitoken=token
            )

            response_text = local_base.PRTG_Get_request(url, asdict(url_params))

            # the response text will have the new sensor ID embedded within it
            # the folloing lines uses regex to pull out that id
            matches = expression.search(response_text)
            new_id = matches.group("sensor_id")
            print(f"{sensor_name} sensor applied to device, with id = {new_id}")
            time.sleep(1.5)

            # When copied, sensor will be paused
            print(f"Activating sensor, {new_id}...")
            resume(core, new_id, token)
            # sleep to allow time for command to execute
            time.sleep(1.5)
            print(f"{sensor_name} sensor = {new_id}")

        print("=====================END=====================")
        print()


# TODO: Add docstring to explain the default return value
# TODO: Add docstring to explain the function of the command, arguments, and return values
@app.command()
def list(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    tags: Annotated[
        List[str], typer.Option(help="Tags listed on associated sensor")
    ] = None,
    name: Annotated[str, typer.Option(help="Name of Sensor being queried")] = None,
    paused: Annotated[
        bool, typer.Option("--paused", help="List only pasused sensors")
    ] = False,
    output: Annotated[
        Output,
        typer.Option(
            "--output", "-o", help="Output format of command", case_sensitive=False
        ),
    ] = Output.text,
) -> List[str]:
    """
    List Sensors based on query parameters.


    If --name is used, value in --tag will be ignored.

    """

    token = config.get_token(core)
    url = local_base.query_url(core)
    # + f"?content=sensors&output=json&columns=objid,name,device&apitoken={token}&count=50000"
    url_params = asdict(QueryParams(columns="objid,name,device", apitoken=token))

    if name is not None:
        device_only = True
        url_params["filter_name"] = name
    elif tags is not None:
        for tag in tags:
            # url = url + f"&filter_tags=@tag({tag})"
            url_params["filter_tags"] = "@tag({tag}"

            if "filter_tags" in url_params:
                url_params["filter_tags"].append("@tag({tag})")
            else:
                url_params["filter_tags"] = ["@tag({tag})"]

    if paused:
        url_params["filter_status"] = ["7", "8"]

    sensors = local_base.PRTG_Get_request(url, url_params)["sensors"]

    sensors = sorted(sensors, key=lambda s: s["name"])
    sensor_ids = " ".join([str(sensor["objid"]) for sensor in sensors])

    if output == Output.table:
        outputs.sensor_table(sensors, device_only)
    else:
        print(sensor_ids)

    print(f"Total Sensors: {len(sensor_ids)}")
    return sensor_ids


@app.command(no_args_is_help=True)
def resume(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    sensor_id: Annotated[str, typer.Argument(help="ID of the sensor to be resumed")],
    token: Annotated[str, typer.Option(help="User token for the given core")] = None,
):
    """
    Resumes metrics gatering on a sensor that is in a non-active statee

    Non-Active states: Unknown, Warning, PausedbyUser, Unussual, PausedUntil, DownAcknowledsge
    """
    sensor_id = sensor_id.split()
    if token is None:
        token = config.get_token(core)

    for sensor in sensor_id:
        url = local_base.base_url(core, action="pause")
        # + f"pause.htm?id={sensor}&action=1&apitoken={token}"
        url_params = asdict(QueryParams(id=sensor, apitoken=token, action=1))
        local_base.PRTG_Get_request(url, url_params)
        time.sleep(3)
        print(f"sensor Activation for, {sensor} is successful")


@app.command(no_args_is_help=True)
def pause(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    sensor_id: Annotated[str, typer.Argument(help="ID of the sensor to be resumed")],
    message: Annotated[str, typer.Option(help="Reason for pausing device")] = None,
    token: Annotated[str, typer.Option(help="User token for the given core")] = None,
):
    """
    Paues metrics gatering on a sensor that in a collecting or up state
    """

    if token is None:
        token = config.get_token(core)

    url = local_base.base_url(core, action="pause")
    # + f"pause.htm?id={sensor_id}&action=0&apitoken={token}"
    url_params = asdict(QueryParams(id=sensor_id, apitoken=token, action=0))

    if message is not None:
        url_params["pausemsg"] = message

    local_base.PRTG_Get_request(url, url_params)
    time.sleep(1.5)


def has_sensor(
    core: str,
    device_id: str,
    token: str = None,
    sensor_id: str = None,
    sensor_name: str = None,
) -> bool:
    """
    Get a list of Devices associated with the a particular sensor.

    Arguments:
       sensor_name:
           name of sensor of interest. value given is case sensitive
        device_id:
            id of the device of interest.

    Returns:
        A list of strings containing the device IDs
    """

    if sensor_name is None:
        if sensor_id is None:
            print("Function needs a sensor id or a sensor name to perform search")
            typer.Exit(code=1)
        else:
            sensor_name = get_sensor_name(sensor_id, core, token)

    if token is None:
        token = config.get_token(core)

    url = local_base.query_url(core)
    # + f"?content=sensors&id={device_id}&output=json&columns=objid,name,device&apitoken={token}&count=50000&filter_name={sensor_name}"
    url_params = asdict(
        QueryParams(
            id=device_id,
            columns="objid,name,device",
            apitoken=token,
            filter_name=sensor_name,
        )
    )

    return (
        True
        if len(local_base.PRTG_Get_request(url, url_params)["sensors"]) > 0
        else False
    )


def get_sensor_name(sensor_id: str, core: str, token: str) -> str:
    url = local_base.query_url(core)
    # + f"?content=sensors&output=json&columns=objid,name,device&apitoken={token}&count=50000&filter_objid={sensor_id}"
    url_params = asdict(
        QueryParams(columns="objid,name,device", apitoken=token, filter_objid=sensor_id)
    )
    return local_base.PRTG_Get_request(url, url_params)["sensors"][0]["name"]


# TODO: Add a command named sensor 'status' that will return sensor data.
