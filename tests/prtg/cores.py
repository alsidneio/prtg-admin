import typer
from typing import List
from enum import Enum

app = typer.Typer(no_args_is_help=True)

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


# TODO figure out how to make this a callback such that you can call the command like so:
# TODO prtg cores --list
@app.command()
def list() -> List[str]:
    """
    List PRTG cores currently configured in the app

    This command takes no arguments.

    prtg cores list
    """
    print("Available cores in infrastructure:")
    print([core.name for core in cores])
