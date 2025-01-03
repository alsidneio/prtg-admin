from rich.console import Console
from rich.table import Table


def sensor_table(sensor_list: list, device_only: bool = False) -> Table:

    table = Table(title="Sensor Status")
    table.add_column("Sensor ID", justify="right")
    table.add_column("Sensor Name", justify="left")

    if not device_only:
        table.add_column("Host Name", justify="right")
        table.add_column("Status", justify="right")
        table.add_column("Message", justify="left")

    for sensor in sensor_list:
        objid = sensor["objid"]
        device = sensor["device"]
        if device_only:
            table.add_row(f"{objid}", f"{device}")
        else:
            table.add_row(
                f" {objid}",
                f"{device}",
                f"{sensor['status']}",
                f"{sensor['message_raw']}",
            )

    console = Console()
    console.print(table)


def device_table(sensor_list: list, include_tags: bool = False):

    table = Table(title="Device List")
    table.add_column("Device ID", justify="center")
    table.add_column("Device Name", justify="center")

    if include_tags:
        table.add_column("Tags", justify="center")

    for device in sensor_list:
        objid = device["objid"]
        server = device["name"]
        if include_tags:
            tags = device["tags"]

        (
            table.add_row(str(objid), server, tags)
            if include_tags
            else table.add_row(str(objid), server)
        )

    console = Console()
    console.print(table)
