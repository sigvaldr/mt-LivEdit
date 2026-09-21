import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from livedit.decal_model import LiveryDocument, DecalParseError
from livedit import operations

SAMPLE = {
    "vehicleKey": "Muhan",
    "decal": {
        "decalLayers": [
            {"decalKey": "first-in-json", "color": {"b": 0, "g": 0, "r": 0, "a": 255},
             "position": {"x": 0.0, "y": 0.0}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
             "decalScale": 1.0, "stretch": 1.0, "coverage": 1, "flags": 264},
            {"decalKey": "second-in-json", "color": {"b": 0, "g": 0, "r": 0, "a": 255},
             "position": {"x": 10.0, "y": 10.0}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
             "decalScale": 2.0, "stretch": 1.0, "coverage": 1, "flags": 264},
        ]
    },
}


def test_parse_valid():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    assert len(doc.layers) == 2


def test_parse_rejects_garbage():
    try:
        LiveryDocument.from_text("not json")
        assert False, "should have raised"
    except DecalParseError:
        pass


def test_parse_rejects_wrong_shape():
    try:
        LiveryDocument.from_text(json.dumps({"foo": "bar"}))
        assert False, "should have raised"
    except DecalParseError:
        pass


def test_display_order_is_reversed():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    rows = doc.display_rows()
    # storage index 1 ("second-in-json") should be shown first (top of in-game list)
    assert rows[0][0] == 1
    assert "second-in-json" in rows[0][1]
    assert rows[1][0] == 0
    assert "first-in-json" in rows[1][1]


def test_move_down_subtracts_y():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[0]
    operations.move([layer], "down", 10)
    assert layer["position"]["y"] == -10.0
    assert layer["position"]["x"] == 0.0


def test_move_up_adds_y():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[0]
    operations.move([layer], "up", 10)
    assert layer["position"]["y"] == 10.0


def test_move_right_and_left():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[0]
    operations.move([layer], "right", 5)
    assert layer["position"]["x"] == 5.0
    operations.move([layer], "left", 5)
    assert layer["position"]["x"] == 0.0


def test_scale_larger():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[1]  # decalScale 2.0
    operations.scale([layer], "larger", 25)
    assert abs(layer["decalScale"] - 2.5) < 1e-9
    assert layer["stretch"] == 1.0  # untouched


def test_scale_smaller():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[1]
    operations.scale([layer], "smaller", 25)
    assert abs(layer["decalScale"] - 1.5) < 1e-9


def test_rotate_clockwise_and_counterclockwise():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    layer = doc.layers[0]
    operations.rotate([layer], "clockwise", 90)
    assert layer["rotation"]["roll"] == 90
    operations.rotate([layer], "counterclockwise", 30)
    assert layer["rotation"]["roll"] == 60


def test_round_trip_preserves_other_fields():
    doc = LiveryDocument.from_text(json.dumps(SAMPLE))
    out = json.loads(doc.to_json())
    assert out["vehicleKey"] == "Muhan"
    assert len(out["decal"]["decalLayers"]) == 2


if __name__ == "__main__":
    import inspect
    failures = 0
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
