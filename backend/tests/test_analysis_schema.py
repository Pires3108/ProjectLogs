from app.analysis.prompt import analysis_json_schema


def test_strict_schema_closes_objects_and_requires_every_property() -> None:
    schema = analysis_json_schema()
    objects = [schema, *schema.get("$defs", {}).values()]

    for item in objects:
        if item.get("type") != "object":
            continue
        assert item["additionalProperties"] is False
        assert set(item["required"]) == set(item["properties"])
