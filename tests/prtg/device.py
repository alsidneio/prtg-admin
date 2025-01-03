import typer
import config
from typing import List, Optional
from typing_extensions import Annotated
import terminal_outputs as outputs
import local_base
from enum import Enum
from rich import print
import xmltodict
from dataclasses import dataclass, asdict

app = typer.Typer(no_args_is_help=True)


class Output(str, Enum):
    text = "text"
    table = "table"


@dataclass
class QueryParams:
    action: Optional[int] = None
    apitoken: Optional[str] = None
    columns: Optional[str] = None
    content: Optional[str] = "devices"
    count: Optional[int] = 50000
    filter_name: Optional[list[str]] = None
    filter_objid: Optional[list[str]] = None
    id: Optional[str] = None
    name: Optional[str] = None
    output: Optional[str] = "json"
    tags: Optional[str] = None
    targetid: Optional[int] = None
    value: Optional[str] = None


# TODO: look into how we are going to solve for multi items for options
# TODO: split --tags options into multi
# TODO: if object ID is given then that overides
# TODO: add an option to filter by device group
# TODO: list still returning all devices even with a given object id filtered


@app.command(no_args_is_help=True)
def list(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    tags: Annotated[
        List[str], typer.Option(help="Tags to used to filter query")
    ] = None,
    ids: Annotated[
        List[str], typer.Option(help="Tags listed on associated devices")
    ] = None,
    output: Annotated[
        Output,
        typer.Option(
            "--output", "-o", help="Output format of command", case_sensitive=False
        ),
    ] = Output.text,
) -> List[str]:
    """
    List Devices within a PRTG Core

    returns a list fof devices IDs
    """
    tags_included = False
    token = config.get_token(core)
    url = local_base.query_url(core)
    url_params = asdict(QueryParams(columns="objid,name,tags", apitoken=token))

    # + f"?content=devices&output=json&count=50000&columns=objid,name,tags&apitoken={token}"

    if ids is not None:
        for id in ids:
            # url = url + f"&filter_objid={id}"
            if "filter_objid" in url_params:
                url_params["filter_objid"].append(id)
            else:
                url_params["filter_objid"] = [id]

    #TODO: do an exception for an unauthorized  code 
    devices = local_base.PRTG_Get_request(url, url_params)["devices"]
    if tags is not None:
        tags_included = True

        for tag in tags:
            devices = [device for device in devices if tag in device["tags"]]

    devices = sorted(devices, key=lambda d: d["name"])
    device_ids = " ".join([str(device["objid"]) for device in devices])

    # TODO: Highlight tag names in the table output
    if output == Output.table:
        outputs.device_table(devices, tags_included)
    else:
        print(device_ids)

    # TODO: Create a test for this output number
    print(f"Total Devices: {len(devices)}")
    return device_ids


# TODO: make a seperate MD page for documentation
# TODO: make an option for case insensitive on the substring search


@app.command()
def search(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    keyword: Annotated[str, typer.Argument(help="Keyword search term")],
    output: Annotated[
        Output,
        typer.Option(
            "--output", "-o", help="Terminal output format", case_sensitive=False
        ),
    ] = Output.text,
) -> List[str]:
    """Search for a device by keyword
    Default terminal output is text and will only  print device ids


    table: will print a table with Object ID, Device Name, and Associated tags

    Returns an array of IDs

    Example:
    prtg device search serveronprem web -o table

    """
    token = config.get_token(core)
    url = local_base.query_url(core)
    url_params = asdict(QueryParams(columns="objid,name,tags", apitoken=token))

    devices = local_base.PRTG_Get_request(url, url_params)["devices"]

    filtered_devices = [device for device in devices if keyword in device["name"]]

    device_ids = [device["objid"] for device in filtered_devices]

    if output == Output.table:
        outputs.device_table(filtered_devices, True)
    else:
        print(*device_ids)

    return device_ids


@app.command(no_args_is_help=True)
def add_tags(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    device_id: Annotated[str, typer.Argument(help="device ID")],
    tags: Annotated[str, typer.Option(help="tags to be added to device ")],
) -> None:
    """
    Add tags to a device or multiple devices
    """
    token = config.get_token(core)
    devices = device_id.split()
    tags = tags.split()

    for device in devices:
        print("===============ADD START================")
        starting_tags = get_tags(core, device)
        starting_tags_list = starting_tags.split()
        current_tags_list = starting_tags.split()

        for tag in tags:
            if tag in starting_tags_list:
                print()
                print(f"The tag: {tag} found on device: {device}, skipping to next tag")
                continue

            current_tags_list.append(tag)

        new_tags = " ".join(current_tags_list)

        if new_tags == starting_tags:
            print("no change in tags detected")
        else:
            apply_tags(core, token, device, new_tags)
            print()
            print("Updated tags")
            print("==================")
            new_tags = get_tags(core, device)
            print()

    return None


@app.command(no_args_is_help=True)
def delete_tags(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    device_id: Annotated[str, typer.Argument(help="Device ID")],
    tags: Annotated[str, typer.Option(help="tags to be removed from Device")],
) -> str | None:
    """
    Delete a tag from a device or a set of devices
    """
    token = config.get_token(core)
    tags = tags.split()
    devices = device_id.split()

    for device in devices:
        print("==========DELETE START================")
        starting_tags = get_tags(core, device)
        current_tags = get_tags(core, device, True)
        for tag in tags:
            print()
            print(f"Checking for tag: {tag}")

            if current_tags.count(tag) == 0:
                print(f"{tag} not found on device: {device}, skipping...")
                continue
            else:
                print()
                print("Removing Tag")
                current_tags = current_tags.replace(tag, "").strip()

        if starting_tags == current_tags:
            print("no change in tags detected")
        else:
            apply_tags(core, token, device, current_tags)
            print()
            print("Updated tags")
            print("==================")
            current_tags = get_tags(core, device)
            print()

    return current_tags


# TODo: make it so that you can input a singular number or string of numbers
@app.command(no_args_is_help=True)
def get_tags(
    core: Annotated[str, typer.Argument(help="PRTG core to connect to")],
    device_id: Annotated[str, typer.Argument(help=" objid of the device")],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Prevents tag status to terminal")
    ] = False,
) -> str | None:
    """
    Get tags that are currently on a Device
    """
    token = config.get_token(core)
    url = local_base.base_url(core, action="get_prop")
    # f"getobjectproperty.htm?id={device_id}&name=tags&apitoken={token}"

    url_params = QueryParams(id=device_id, apitoken=token, name="tags")

    # This returns an xml response that needs to be parsed
    tags_xml = local_base.PRTG_Get_request(url, asdict(url_params))

    tags = xmltodict.parse(tags_xml)["prtg"]

    # TODO: this try/catch  needs to be a function of its own with `getobjectproperty`
    try:
        # TODO: write a testcase for this happy path
        tags = tags["result"]

    except KeyError:
        # TODO: Write a testcase for this error
        print(f"[bold red]{tags['error']}")
        tags = None
    else:
        # Status to terminal
        if not quiet:
            print(f"Tags for Device ID: {device_id}")
            print(tags)

    return tags


# ========================= Helper Functions===================================


def apply_tags(core: str, token: str, device_id=str, tags=str):
    url = local_base.base_url(core, action="set_prop")
    # + f"setobjectproperty.htm?id={device_id}&name=tags&value={tags}&apitoken={token}"
    url_params = asdict(
        QueryParams(id=device_id, name="tags", value=tags, apitoken=token)
    )

    local_base.PRTG_Get_request(url, url_params)


def remove_duplicate_tags(core: str, device_id: str) -> str:
    device = device_id

    tags = get_tags(core, device, quiet=True)
    taglist = tags.split()

    # Looping through tags
    for tag in taglist:
        if tags.count(tag) > 1:
            tags = tags.replace(tag, "").strip()

    print(f"Device only tags: {tags}")
    return tags
