from dataclasses import dataclass, asdict
from pathlib import Path
import time
from typing import Optional
import typer
import config
from rich import print
from typing_extensions import Annotated
import local_base
import csv
import xmltodict


app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")


@dataclass
class QueryParams:
    action: Optional[int] = None
    apitoken: Optional[str] = None
    columns: Optional[str] = None
    content: Optional[str] = None
    count: Optional[str] = None
    filter_name: Optional[str] = None
    filter_objid: Optional[str] = None
    filter_tags: Optional[list[str]] = None
    id: Optional[str] = None
    name: Optional[str] = None
    output: Optional[str] = None
    subtype: Optional[str] = "channel"
    subid: Optional[int] = None
    targetid: Optional[int] = None
    value: Optional[str] = None


# setobjectproperty.htm?id=[OBJID]&subtype=channel&subid=0&name=limitmode&value=0
@app.command(no_args_is_help=True)
def state(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    subid: Annotated[str, typer.Option(help="channel ID")],
    sensor_id: Annotated[str, typer.Option(help="ID of the target sensor")] = None,
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            "-f",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="File to read in object IDs",
        ),
    ] = None,
    token: Annotated[str, typer.Option(help="User token for the given core")] = None,
    enable: Annotated[
        bool, typer.Option("--enable", help="Enables the channel limits")
    ] = False,
    disable: Annotated[
        bool, typer.Option("--disable", help="Disables the channel limits")
    ] = False,
) -> None:
    """set or list the state of a sensor channel

    [Examples]
    - Listing the current state of multiple sensors
    prtg channel state serveronprem --subid 0 --sensor_id "54321 25964 45789 32147"

    - Pausing the current thresholds of a list of sensors using a file
    prtg channel state serveronprem --subid 0 --disable --file=./some/path.csv

    - Enabling the current thresholds of a list of sensors using a file
    prtg channel state serveronprem --subid 0 --enable --file=./some/path.csv

    Note:
        1. Values on --sensor_id take preceedent over --file values
        2. Only comma delimited csv files are supported at this time

    Returns:
        None
    """

    if sensor_id is None and file is None:
        print("Missing Arguments")
        print("Must enter sensor_id via the --sensor_id or --file flag")
        raise typer.Exit(1)

    # TODO: add functionality to take each id and run the request, Might need to make its own function
    if sensor_id is not None:
        file = None

    # reading in given file
    f = open(file, "r")
    reader = csv.DictReader(f, delimiter=",")

    token = config.get_token(core)

    url_params = asdict(QueryParams(subid=subid, apitoken=token))

    if enable or disable:
        url_params["value"] = 1 if enable else 0
        action = "Enabling" if enable else "Pausing"
        url = local_base.base_url(core, action="set_prop")

        for row in reader:
            objid = row["objid"]
            print(f"{action} channel: {url_params['subid']} for sensor: {objid}")
            url_params["id"] = objid
            local_base.PRTG_Get_request(url, url_params)
            print()
    else:
        print("Current Channel Status ")
        print("===============")
        # TODO: i want the action param to fill with predetermined values
        url = local_base.base_url(core, action="get_prop")
        for row in reader:
            objid = row["objid"]
            url_params["id"] = objid
            limit_xml = local_base.PRTG_Get_request(url, url_params)
            status = xmltodict.parse(limit_xml)["prtg"]

            # TODO: this try/catch  needs to be a function of its own with `getobjectproperty`
            try:
                # TODO: write a testcase for this happy path
                print(f"For Sensor {objid}, threshold is: {status['result']}")

            except KeyError:
                # TODO: Write a testcase for this error
                print(f"[bold red]{status['error']}")

            print()
    # Closing the file to prevent Error
    f.close()


@app.command(no_args_is_help=True)
def set_threshold(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    subid: Annotated[str, typer.Option(help="channel ID")],
    value: Annotated[int, typer.Option(help="Set the threshold value")],
    sensor_id: Annotated[str, typer.Option(help="ID of the target sensor")] = None,
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            "-f",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="File to read in object IDs",
        ),
    ] = None,
    token: Annotated[str, typer.Option(help="User token for the given core")] = None,
    warning: Annotated[
        bool, typer.Option("--warning", help="Sets the warning threshold")
    ] = False,
    error: Annotated[
        bool, typer.Option("--error", help="Sets the error threshold")
    ] = False,
) -> None:

    if sensor_id is None and file is None:
        print("Missing Arguments")
        print("Must enter sensor_id via the --sensor_id or --file flag")
        raise typer.Exit(1)

    if not warning and not error:
        print(
            "Please enter the type of limit being set with the --warning or --error flag"
        )
        raise typer.Exit(1)

    if warning and error:
        print("Only one type of limit can be set per command line entry")
        raise typer.Exit(1)

    # TODO: add functionality to take each id and run the request, Might need to make its own function
    if sensor_id is not None:
        file = None

    # reading in given file
    f = open(file, "r")
    reader = csv.DictReader(f, delimiter=",")

    token = config.get_token(core)
    url = local_base.base_url(core, action="set_prop")
    url_params = asdict(QueryParams(value=value, subid=subid, apitoken=token))

    for row in reader:
        objid = row["objid"]
        url_params["id"] = objid
        url_params["name"] = "limitminwarning" if warning else "limitminerror"
        url_params['value'] = value
        print(
            f"Applying {url_params['name']} threshold to channel: {url_params['subid']} for sensor: {objid}"
        )
        # set the threshold
        local_base.PRTG_Get_request(url, url_params)
        time.sleep(.5)

        print(
            f"Enabling {url_params['name']} threshold to channel: {url_params['subid']} for sensor: {objid}"
        )
        url_params["name"] = "limitmode"
        url_params["value"] = 1
        local_base.PRTG_Get_request(url, url_params)
        time.sleep(.5)
        print()

    f.close()
