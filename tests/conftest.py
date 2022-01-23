# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import platform
import socket

import pytest
import redis
from packaging import version

import coredis
import coredis.sentinel

REDIS_VERSIONS = {}


@pytest.fixture(scope="session", autouse=True)
def uvloop():
    if os.environ.get("COREDIS_UVLOOP") == "True":
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def check_min_version(request, client):
    if client not in REDIS_VERSIONS:
        if isinstance(client, coredis.StrictRedisCluster):
            info = list((await client.info()).values()).pop()
            REDIS_VERSIONS[client] = version.parse(info["redis_version"])
        else:
            REDIS_VERSIONS[client] = version.parse(
                (await client.info())["redis_version"]
            )

    for marker in request.node.iter_markers():
        if marker.name == "min_server_version" and marker.args:
            if REDIS_VERSIONS[client] < version.parse(marker.args[0]):
                return pytest.skip(f"Skipped for versions < {marker.args[0]}")

        if marker.name == "nocluster" and isinstance(
            client, coredis.StrictRedisCluster
        ):
            return pytest.skip("Skipped for redis cluster")

        if marker.name == "clusteronly" and not isinstance(
            client, coredis.StrictRedisCluster
        ):
            return pytest.skip("Skipped for non redis cluster")


def check_redis_cluster_ready(host, port):
    try:
        return len(redis.Redis(host, 7000).cluster("slots")) == 3
    except Exception:
        return False


def check_sentinel_auth_ready(host, port):
    return ping_socket(host, 36379)


def ping_socket(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host, port))

        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()

    return ip


@pytest.fixture(scope="session")
def host_ip_env(host_ip):
    os.environ["HOST_IP"] = str(host_ip)


@pytest.fixture(scope="session")
def docker_services(host_ip_env, docker_services):
    return docker_services


@pytest.fixture(scope="session")
def redis_basic_server(docker_services):
    docker_services.start("redis-basic")
    docker_services.wait_for_service("redis-basic", 6379, ping_socket)
    yield ["localhost", 6379]


@pytest.fixture(scope="session")
def redis_uds_server(docker_services):
    if platform.system().lower() == "darwin":
        pytest.skip("Fixture not supported on OSX")
    docker_services.start("redis-uds")
    yield "/tmp/limits.redis.sock"


@pytest.fixture(scope="session")
def redis_auth_server(docker_services):
    docker_services.start("redis-auth")
    yield ["localhost", 6389]


@pytest.fixture(scope="session")
def redis_ssl_server(docker_services):
    docker_services.start("redis-ssl")
    yield


@pytest.fixture(scope="session")
def redis_cluster_server(docker_services):
    docker_services.start("redis-cluster-init")
    docker_services.wait_for_service("redis-cluster-6", 7005, check_redis_cluster_ready)
    yield


@pytest.fixture(scope="session")
def redis_sentinel_server(docker_services):
    docker_services.start("redis-sentinel")
    docker_services.wait_for_service("redis-sentinel", 26379, ping_socket)

    return coredis.sentinel.Sentinel([("localhost", 26379)])


@pytest.fixture(scope="session")
def redis_sentinel_auth_server(docker_services):
    docker_services.start("redis-sentinel-auth")
    docker_services.wait_for_service(
        "redis-sentinel-auth", 26379, check_sentinel_auth_ready
    )
    yield


@pytest.fixture
async def redis_basic(redis_basic_server, request):
    client = coredis.StrictRedis("localhost", 6379)
    await check_min_version(request, client)
    await client.flushall()
    await client.config_set("maxmemory-policy", "noeviction")

    return client


@pytest.fixture
async def redis_ssl(redis_ssl_server, request):
    storage_url = (
        "rediss://localhost:8379/0?ssl_cert_reqs=required"
        "&ssl_keyfile=./tests/tls/client.key"
        "&ssl_certfile=./tests/tls/client.crt"
        "&ssl_ca_certs=./tests/tls/ca.crt"
    )
    client = coredis.StrictRedis.from_url(storage_url)
    await check_min_version(request, client)
    await client.flushall()
    await client.config_set("maxmemory-policy", "noeviction")

    return client


@pytest.fixture
async def redis_auth(redis_auth_server, request):
    client = coredis.StrictRedis.from_url(
        f"redis://:sekret@{redis_auth_server[0]}:{redis_auth_server[1]}"
    )
    await check_min_version(request, client)
    await client.flushall()
    await client.config_set("maxmemory-policy", "noeviction")

    return client


@pytest.fixture
async def redis_uds(redis_uds_server, request):
    client = coredis.StrictRedis.from_url(f"unix://{redis_uds_server}")
    await check_min_version(request, client)
    await client.flushall()
    await client.config_set("maxmemory-policy", "noeviction")

    return client


@pytest.fixture
async def redis_cluster(redis_cluster_server, request):
    cluster = coredis.StrictRedisCluster("localhost", 7000, stream_timeout=10)
    await check_min_version(request, cluster)
    await cluster.flushall()
    await cluster.flushdb()
    await cluster.config_set("maxmemory-policy", "noeviction")

    yield cluster

    cluster.connection_pool.disconnect()


@pytest.fixture
async def redis_sentinel(redis_sentinel_server, request):
    sentinel = coredis.sentinel.Sentinel(
        [("localhost", 26379)],
        sentinel_kwargs={},
    )
    master = sentinel.master_for("localhost-redis-sentinel")
    await check_min_version(request, master)
    await master.flushall()

    return sentinel


@pytest.fixture
async def redis_sentinel_auth(redis_sentinel_auth_server, request):
    sentinel = coredis.sentinel.Sentinel(
        [("localhost", 36379)],
        sentinel_kwargs={"password": "sekret"},
        password="sekret",
    )
    master = sentinel.master_for("localhost-redis-sentinel")
    await check_min_version(request, master)
    await master.flushall()

    return sentinel


@pytest.fixture(scope="session")
def docker_services_project_name():
    return "coredis"


@pytest.fixture(scope="session")
def docker_compose_files(pytestconfig):
    """Get the docker-compose.yml absolute path.
    Override this fixture in your tests if you need a custom location.
    """

    return ["docker-compose.yml"]


def targets(*targets):
    return pytest.mark.parametrize(
        "client", [pytest.lazy_fixture(target) for target in targets]
    )


@pytest.fixture
def redis_server_time():
    async def _get_server_time(client):
        if isinstance(client, coredis.StrictRedisCluster):
            client_times = await client.time()
            seconds, milliseconds = list(client_times.values())[0]
        elif isinstance(client, coredis.StrictRedis):
            seconds, milliseconds = await client.time()
        timestamp = float("%s.%s" % (seconds, milliseconds))

        return datetime.datetime.fromtimestamp(timestamp)

    return _get_server_time
