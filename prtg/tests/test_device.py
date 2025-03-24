import importlib
import re
from typer.testing import CliRunner


runner = CliRunner()
local_base = importlib.import_module("local_base")


def test_device_list():
    result = runner.invoke(local_base.app, ["device", "list", "serveronprem"])
    assert result.exit_code == 0
    assert "Total Devices" in result.stdout


def test_device_list_tag():
    base_result = runner.invoke(local_base.app, ["device", "list", "serveronprem"])
    tagged_result = runner.invoke(
        local_base.app, ["device", "list", "serveronprem", "--tags", "role:webserver"]
    )
    assert tagged_result.exit_code == 0
    assert "Total Devices" in tagged_result.stdout
    tagged_num = parse_device_num(tagged_result.stdout)
    base_num = parse_device_num(base_result.stdout)
    assert base_num > tagged_num

def test_device_search(): 
    result = runner.invoke(local_base.app, ["device", "search", "serveronprem","web"])
    assert result.exit_code == 0
    assert "Total Devices" in result.stdout

def parse_device_num(input: str):
    match = re.search(r"Total Devices: (?P<dev_count>\d+)", input)
    return match.groupdict()["dev_count"]
