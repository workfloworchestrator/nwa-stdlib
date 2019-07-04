from itertools import dropwhile
from pathlib import Path

from nwastdlib.swagger import SwaggerFile
from ruamel.yaml import YAML

tests_base_path = next(dropwhile(lambda p: p.name != "tests", Path(__file__).parents))


def test_set_host():
    swagger_file = tests_base_path / "data" / "petstore-simple.yaml"
    yaml = YAML(typ="safe")
    swagger_def = yaml.load(swagger_file)
    assert swagger_def["host"] == "petstore.swagger.io"

    temp_swagger_file = SwaggerFile(swagger_file).set_host("fubar.org").write()
    with open(temp_swagger_file.value) as f:
        temp_swagger_def = yaml.load(f)
    assert temp_swagger_def["host"] == "fubar.org"
