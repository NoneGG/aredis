# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

# 3rd party imports
import pytest

# rediscluster imports
from coredis.commands.cluster import parse_cluster_slots
from coredis.exceptions import ClusterDownError, RedisClusterException
from coredis.utils import (
    b,
    blocked_command,
    clusterdown_wrapper,
    dict_merge,
    first_key,
    list_keys_to_dict,
    merge_result,
)


def test_parse_cluster_slots():
    """
    Example raw output from redis cluster. Output is form a redis 3.2.x node
    that includes the id in the reponse. The test below that do not include the id
    is to validate that the code is compatible with redis versions that do not contain
    that value in the response from the server.

    127.0.0.1:10000> cluster slots
    1) 1) (integer) 5461
       2) (integer) 10922
       3) 1) "10.0.0.1"
          2) (integer) 10000
          3) "3588b4cf9fc72d57bb262a024747797ead0cf7ea"
       4) 1) "10.0.0.4"
          2) (integer) 10000
          3) "a72c02c7d85f4ec3145ab2c411eefc0812aa96b0"
    2) 1) (integer) 10923
       2) (integer) 16383
       3) 1) "10.0.0.2"
          2) (integer) 10000
          3) "ffd36d8d7cb10d813f81f9662a835f6beea72677"
       4) 1) "10.0.0.5"
          2) (integer) 10000
          3) "5c15b69186017ddc25ebfac81e74694fc0c1a160"
    3) 1) (integer) 0
       2) (integer) 5460
       3) 1) "10.0.0.3"
          2) (integer) 10000
          3) "069cda388c7c41c62abe892d9e0a2d55fbf5ffd5"
       4) 1) "10.0.0.6"
          2) (integer) 10000
          3) "dc152a08b4cf1f2a0baf775fb86ad0938cb907dc"
    """

    extended_mock_response = [
        [
            0,
            5460,
            ["172.17.0.2", 7000, "ffd36d8d7cb10d813f81f9662a835f6beea72677"],
            ["172.17.0.2", 7003, "5c15b69186017ddc25ebfac81e74694fc0c1a160"],
        ],
        [
            5461,
            10922,
            ["172.17.0.2", 7001, "069cda388c7c41c62abe892d9e0a2d55fbf5ffd5"],
            ["172.17.0.2", 7004, "dc152a08b4cf1f2a0baf775fb86ad0938cb907dc"],
        ],
        [
            10923,
            16383,
            ["172.17.0.2", 7002, "3588b4cf9fc72d57bb262a024747797ead0cf7ea"],
            ["172.17.0.2", 7005, "a72c02c7d85f4ec3145ab2c411eefc0812aa96b0"],
        ],
    ]

    parse_cluster_slots(extended_mock_response)

    extended_mock_binary_response = [
        [
            0,
            5460,
            [b("172.17.0.2"), 7000, b("ffd36d8d7cb10d813f81f9662a835f6beea72677")],
            [b("172.17.0.2"), 7003, b("5c15b69186017ddc25ebfac81e74694fc0c1a160")],
        ],
        [
            5461,
            10922,
            [b("172.17.0.2"), 7001, b("069cda388c7c41c62abe892d9e0a2d55fbf5ffd5")],
            [b("172.17.0.2"), 7004, b("dc152a08b4cf1f2a0baf775fb86ad0938cb907dc")],
        ],
        [
            10923,
            16383,
            [b("172.17.0.2"), 7002, b("3588b4cf9fc72d57bb262a024747797ead0cf7ea")],
            [b("172.17.0.2"), 7005, b("a72c02c7d85f4ec3145ab2c411eefc0812aa96b0")],
        ],
    ]

    extended_mock_parsed = {
        (0, 5460): [
            {
                "host": b"172.17.0.2",
                "node_id": b"ffd36d8d7cb10d813f81f9662a835f6beea72677",
                "port": 7000,
                "server_type": "master",
            },
            {
                "host": b"172.17.0.2",
                "node_id": b"5c15b69186017ddc25ebfac81e74694fc0c1a160",
                "port": 7003,
                "server_type": "slave",
            },
        ],
        (5461, 10922): [
            {
                "host": b"172.17.0.2",
                "node_id": b"069cda388c7c41c62abe892d9e0a2d55fbf5ffd5",
                "port": 7001,
                "server_type": "master",
            },
            {
                "host": b"172.17.0.2",
                "node_id": b"dc152a08b4cf1f2a0baf775fb86ad0938cb907dc",
                "port": 7004,
                "server_type": "slave",
            },
        ],
        (10923, 16383): [
            {
                "host": b"172.17.0.2",
                "node_id": b"3588b4cf9fc72d57bb262a024747797ead0cf7ea",
                "port": 7002,
                "server_type": "master",
            },
            {
                "host": b"172.17.0.2",
                "node_id": b"a72c02c7d85f4ec3145ab2c411eefc0812aa96b0",
                "port": 7005,
                "server_type": "slave",
            },
        ],
    }

    assert parse_cluster_slots(extended_mock_binary_response) == extended_mock_parsed


def test_list_keys_to_dict():
    def mock_true():
        return True

    assert list_keys_to_dict(["FOO", "BAR"], mock_true) == {
        "FOO": mock_true,
        "BAR": mock_true,
    }


def test_dict_merge():
    a = {"a": 1}
    b = {"b": 2}
    c = {"c": 3}
    assert dict_merge(a, b, c) == {"a": 1, "b": 2, "c": 3}


def test_dict_merge_empty_list():
    assert dict_merge([]) == {}


def test_blocked_command():
    with pytest.raises(RedisClusterException) as ex:
        blocked_command(None, "SET")
    assert str(ex.value) == "Command: SET is blocked in redis cluster mode"


def test_merge_result():
    assert merge_result({"a": [1, 2, 3], "b": [4, 5, 6]}) == [1, 2, 3, 4, 5, 6]
    assert merge_result({"a": [1, 2, 3], "b": [1, 2, 3]}) == [1, 2, 3]


def test_merge_result_value_error():
    with pytest.raises(ValueError):
        merge_result([])


def test_first_key():
    assert first_key({"foo": 1}) == 1

    with pytest.raises(RedisClusterException) as ex:
        first_key({"foo": 1, "bar": 2})
    assert str(ex.value).startswith("More then 1 result from command")


def test_first_key_value_error():
    with pytest.raises(ValueError):
        first_key(None)


@pytest.mark.asyncio(forbid_global_loop=True)
async def test_clusterdown_wrapper():
    @clusterdown_wrapper
    def bad_func():
        raise ClusterDownError("CLUSTERDOWN")

    with pytest.raises(ClusterDownError) as cex:
        await bad_func()
    assert str(cex.value).startswith("CLUSTERDOWN error. Unable to rebuild the cluster")
