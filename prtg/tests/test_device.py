from unittest import result
import typer
import importlib
from typer.testing import CliRunner




runner = CliRunner()
local_base = importlib.import_module('local_base')


def test_device_list():
    result = runner.invoke(local_base.app, ["device", "list", "serveronprem"])
    assert result.exit_code == 0 
    assert "Total Devices" in result.stdout

def test_device_