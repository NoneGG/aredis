# -*- coding: utf-8 -*-

# python std lib
from __future__ import with_statement

# 3rd party imports
import pytest

# rediscluster imports
from coredis.exceptions import ClusterDownError, RedisClusterException
from coredis.utils import (
    blocked_command,
    clusterdown_wrapper,
    dict_merge,
    first_key,
    list_keys_to_dict,
    merge_result,
)


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


@pytest.mark.asyncio()
async def test_clusterdown_wrapper():
    @clusterdown_wrapper
    def bad_func():
        raise ClusterDownError("CLUSTERDOWN")

    with pytest.raises(ClusterDownError) as cex:
        await bad_func()
    assert str(cex.value).startswith("CLUSTERDOWN error. Unable to rebuild the cluster")
