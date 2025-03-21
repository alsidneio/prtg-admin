import typer
import configparser as cfp
import os
from platformdirs import user_config_dir
from typing_extensions import Annotated


app = typer.Typer(no_args_is_help=True)
config = cfp.ConfigParser()
configdir = user_config_dir()
configfile = "prtg_admin.cfg"
config_file_path = f"{configdir}/{configfile}"

# TODO: allow the option to set a default core to query from 
# TODO: create functionality to allow context/ core switching

def create_config_file():

    config["Tokens"] = {
        "serveronprem": f'{os.getenv("PRTG_TOKEN")}',
        "networkdc": f'{os.getenv("NETWORKDC_TOKEN")}',
        "networkremote-1": f'{os.getenv("NETWORKREMOTE1_TOKEN")}',
        "networkremote-2": f'{os.getenv("NETWORKREMOTE2_TOKEN")}',
        "serveresx": f'{os.getenv("SERVERESX_TOKEN")}',
        "serverazure": f'{os.getenv("SERVERAZURE_TOKEN")}',
        "nttdevices": f'{os.getenv("NTTDEVICES_TOKEN")}',
    }

    with open(config_file_path, "w") as configfile:
        config.write(configfile)

    print(read_config_file())


def read_config_file(quiet: bool = False):
    config.read(config_file_path)

    if not quiet:
        print("Current Config values")
        print("==========================")
        for k, v in config["Tokens"].items():
            print(f"{k} : {v}")


def get_token(core: str) -> str:
    read_config_file(quiet=True)

    token = config["Tokens"][core]

    if token is not None:
        return token
    else:
        print(f"No Auth Token found, please set token for {core}")


@app.command(help="Lists all the current config values")
def list():
    try:
        config.read_file(open(config_file_path))
    except FileNotFoundError:
        print(f"Config file not found, creating file in the the {configdir}")
        create_config_file()
    else:
        print(f"config file location: {configdir}/prtg_admin.cfg")
        print(read_config_file())


@app.command(help="Set values in the config file", no_args_is_help=True)
def set(
    core: Annotated[str, typer.Argument(help="Token to be updated")] = None,
    value: Annotated[str, typer.Argument(help="Token value")] = None,
):
    core = core.lower()
    read_config_file(quiet=True)

    config["Tokens"][core] = value

    with open(config_file_path, "w") as configfile:
        config.write(configfile)

    print(read_config_file())
