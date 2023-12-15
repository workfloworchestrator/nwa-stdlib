import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from nwastdlib.vlans import VlanRanges


def test_vlan_ranges_instantiation():
    assert VlanRanges() == VlanRanges([])
    assert VlanRanges(None) == VlanRanges([])
    assert VlanRanges("") == VlanRanges([])
    assert VlanRanges(4) == VlanRanges("4")
    assert VlanRanges("0") == VlanRanges([(0, 0)]) == VlanRanges([[0]])
    assert VlanRanges("2,4,8") == VlanRanges([(2, 2), (4, 4), (8, 8)]) == VlanRanges([[2], [4], [8]])
    assert VlanRanges("80-120") == VlanRanges([(80, 120)]) == VlanRanges([[80, 120]])
    assert VlanRanges("10,12-16") == VlanRanges([(10, 10), (12, 16)]) == VlanRanges([[10], [12, 16]])

    # String interpretation is quite flexible, allowing extra whitespace
    assert VlanRanges("  4   , 6-   10") == VlanRanges("4,6-10")

    # Overlapping ranges will be normalized
    assert VlanRanges("4,6-9,7-10") == VlanRanges("4,6-10")
    assert VlanRanges([[4], [6, 9], [7, 10]]) == VlanRanges([[4], [6, 10]])

    # Non-sensical ranges are not an error perse
    assert VlanRanges("10-1") == VlanRanges("")


def test_vlan_ranges_str_repr():
    vr = VlanRanges("10-14,4,200-256")

    # `str` version of VlanRanges should be suitable value for constructor, resulting in equivalent object
    assert vr == VlanRanges(str(vr))

    # `repr` version of VlanRanges should be valid Python code resulting in equivalent object
    vr_from_repr = eval(repr(vr), globals(), locals())  # noqa: S307 Use of possibly insecure function
    assert vr_from_repr == vr


@pytest.mark.parametrize(
    "vlan, expected",
    [
        (10, True),
        (20, True),
        (9, False),
        (21, False),
        (0, False),
    ],
)
def test_vlan_ranges_in(vlan, expected):
    vr = VlanRanges("10-20")
    assert bool(vlan in vr) is expected


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", False),
        ("9-10", True),
        ("21-23", False),
        ("20-23", True),
        ("10-20", True),
        ("11-19", True),
        ("0-3,10,20,21-28", True),
        ("0-3,20", True),
        ("0-3,9,21,22-30", False),
    ],
)
def test_vlan_ranges_intersects(vlans, expected):
    vr = VlanRanges("10-20")
    assert bool(vr & VlanRanges(vlans)) is expected


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", "10-20"),
        ("9-10", "11-20"),
        ("21-23", "10-20"),
        ("20-23", "10-19"),
        ("10-20", ""),
        ("11-19", "10,20"),
        ("0-3,10,20,21-28", "11-19"),
        ("0-3,20", "10-19"),
        ("0-3,9,21,22-30", "10-20"),
    ],
)
def test_vlan_ranges_sub(vlans, expected):
    vr = VlanRanges("10-20")
    assert vr - VlanRanges(vlans) == VlanRanges(expected)


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", ""),
        ("9-10", "10"),
        ("21-23", ""),
        ("20-23", "20"),
        ("10-20", "10-20"),
        ("11-19", "11-19"),
        ("0-3,10,20,21-28", "10,20"),
        ("0-3,20", "20"),
        ("0-3,9,21,22-30", ""),
    ],
)
def test_vlan_ranges_and(vlans, expected):
    vr = VlanRanges("10-20")
    assert vr & VlanRanges(vlans) == VlanRanges(expected)


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", "8-20"),
        ("9-10", "9-20"),
        ("21-23", "10-23"),
        ("20-23", "10-23"),
        ("10-20", "10-20"),
        ("11-19", "10-20"),
        ("0-3,10,20,21-28", "0-3,10-28"),
        ("0-3,20", "0-3,10-20"),
        ("0-3,9,21,22-30", "0-3,9-30"),
    ],
)
def test_vlan_ranges_or(vlans, expected):
    vr = VlanRanges("10-20")
    assert vr | VlanRanges(vlans) == VlanRanges(expected)


def test_vlan_ranges_union():
    vr = VlanRanges("10-20")
    # with iterable
    assert vr == VlanRanges().union(VlanRanges("10-15"), [16, 17, 18], (19,), VlanRanges(20))

    # single arg
    assert vr == VlanRanges("10-19").union(VlanRanges(20))


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", "8-20"),
        ("9-10", "9,11-20"),
        ("21-23", "10-23"),
        ("20-23", "10-19,21-23"),
        ("10-20", ""),
        ("11-19", "10,20"),
        ("0-3,10,20,21-28", "0-3,11-19,21-28"),
        ("0-3,20", "0-3,10-19"),
        ("0-3,9,21,22-30", "0-3,9-30"),
    ],
)
def test_vlan_ranges_xor(vlans, expected):
    vr = VlanRanges("10-20")
    assert vr ^ VlanRanges(vlans) == VlanRanges(expected)


@pytest.mark.parametrize(
    "vlans, expected",
    [
        ("8-9", False),
        ("9-10", False),
        ("21-23", False),
        ("20-23", False),
        ("10-20", False),
        ("11-19", True),
        ("0-3,10,20,21-28", False),
        ("0-3,20", False),
        ("0-3,9,21,22-30", False),
    ],
)
def test_vlan_ranges_lt(vlans, expected):
    vr = VlanRanges("10-20")
    assert (VlanRanges(vlans) < vr) is expected


def test_vlan_ranges_hash():
    vr = VlanRanges("10-14,4,200-256")
    # Just making sure it doesn't raise an exception. Which, BTW will be raised, should the internal representation
    # be changed to a mutable data structure.
    assert hash(vr)


def test_vlan_ranges_serialization_deserialization():
    vr = VlanRanges("3,4-10")
    vr2 = VlanRanges(vr.__json__())
    assert vr == vr2


@pytest.mark.parametrize(
    "value",
    [
        "-10",  # Negative values, however, are an error
        "foobar",
    ],
)
def test_vlan_ranges_validations(value):
    # Negative values, however, are an error
    with pytest.raises(ValueError):
        VlanRanges(value)


def test_vlan_ranges_basemodel_validations_ok():
    class TestVlanRanges(BaseModel):
        vlanrange: VlanRanges

    assert TestVlanRanges(vlanrange="12").vlanrange == VlanRanges(12)


@pytest.mark.parametrize("value", ["-30", "bla", "5000"])  # Negative values, however, are an error
def test_vlan_ranges_basemodel_validations_nok(value):
    class TestVlanRanges(BaseModel):
        vlanrange: VlanRanges

    with pytest.raises(ValueError):
        TestVlanRanges(vlanrange=value)


@pytest.mark.parametrize(
    "vrange,expectedlist",
    [("3", [3]), ("3-5,10", [3, 4, 5, 10])],
)
def test_vlan_ranges_schema_generation(vrange, expectedlist):
    """Test that schema generation works."""

    class MyModel(BaseModel):
        vlanranges: VlanRanges

    model = MyModel(vlanranges=f"{vrange}")
    assert isinstance(model.model_dump()["vlanranges"], VlanRanges)
    assert model.model_dump_json() == '{"vlanranges":"%s"}' % (vrange,)
    assert model.model_json_schema() == {
        "properties": {
            "vlanranges": {
                "title": "Vlanranges",
                "type": "string",
                "format": "vlan",
                "pattern": "^([1-4][0-9]{0,3}(-[1-4][0-9]{0,3})?,?)+$",
                "examples": ["345", "20-23,45,50-100"],
            },
        },
        "required": ["vlanranges"],
        "title": "MyModel",
        "type": "object",
    }
    assert list(model.vlanranges) == expectedlist


@pytest.mark.parametrize(
    "value",
    [
        10,
        "11",
        VlanRanges(12),
        [13, 14],
        {15, 16},
        [[17], (18, 19)],
    ],
)
def test_vlan_ranges_validator_ok(value):
    class MyModel(BaseModel):
        vr: VlanRanges

    assert isinstance(MyModel(vr=value).vr, VlanRanges)


@pytest.mark.parametrize(
    "value,exc",
    [
        ("foo", ValidationError),
        (["bar"], ValidationError),
        ([1, "a"], TypeError),
    ],
)
def test_vlan_ranges_validator_error(value, exc):
    class MyModel(BaseModel):
        vr: VlanRanges

    with pytest.raises(exc):
        MyModel(vr=value)


def test_fastapi_serialization_dynamic_model(fastapi_test_client):
    """Test serializing VlanRanges in a dynamic FastAPI response model."""

    class DynamicModel(BaseModel):
        name: str
        model_config = ConfigDict(extra="allow")

    @fastapi_test_client.app.get("/dynamic_model", response_model=DynamicModel)
    def get_dummy_model():
        return {"name": "DummyModel", "vlanrange": VlanRanges(10)}

    response = fastapi_test_client.get("/dynamic_model")
    assert response.json() == {"name": "DummyModel", "vlanrange": "10"}
