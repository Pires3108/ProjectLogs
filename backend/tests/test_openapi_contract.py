from pathlib import Path

import yaml

from app.main import app


def test_versioned_contract_contains_every_executable_operation() -> None:
    contract_path = Path(__file__).parents[2] / "docs" / "openapi.yaml"
    versioned = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    generated = app.openapi()

    versioned_operations = {
        operation["operationId"]
        for path in versioned["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }
    generated_operations = {
        operation["operationId"]
        for path in generated["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }

    assert versioned_operations == generated_operations
