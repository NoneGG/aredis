import pytest

from coredis import DataError, RedisError
from tests.conftest import targets


@targets("redis_basic", "redis_cluster")
@pytest.mark.asyncio()
class TestGeo:
    async def test_geoadd(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        assert await client.geoadd("barcelona", *values) == 2
        assert await client.zcard("barcelona") == 2

    async def test_geoadd_invalid_params(self, client):
        with pytest.raises(RedisError):
            await client.geoadd("barcelona", *(1, 2))

    async def test_geodist(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        assert await client.geoadd("barcelona", *values) == 2
        assert await client.geodist("barcelona", "place1", "place2") == 3067.4157

    async def test_geodist_units(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.geodist("barcelona", "place1", "place2", "km") == 3.0674

    async def test_geodist_invalid_units(self, client):
        with pytest.raises(RedisError):
            assert await client.geodist("x", "y", "z", "inches")

    async def test_geohash(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.geohash("barcelona", "place1", "place2") == [
            b"sp3e9yg3kd0",
            b"sp3e9cbc3t0",
        ]

    async def test_geopos_no_value(self, client):
        assert await client.geopos("barcelona", "place1", "place2") == [None, None]

    async def test_geopos(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        # redis uses 52 bits precision, hereby small errors may be introduced.
        assert await client.geopos("barcelona", "place1", "place2") == [
            (2.19093829393386841, 41.43379028184083523),
            (2.18737632036209106, 41.40634178640635099),
        ]

    @pytest.mark.min_server_version("6.2.0")
    @pytest.mark.nocluster
    async def test_geosearch(self, client):
        values = (
            (2.1909389952632, 41.433791470673, "place1")
            + (2.1873744593677, 41.406342043777, "上海市")
            + (2.583333, 41.316667, "place3")
        )
        await client.geoadd("barcelona", *values)
        assert await client.geosearch(
            "barcelona", longitude=2.191, latitude=41.433, radius=1000
        ) == ["place1"]
        assert await client.geosearch(
            "barcelona", longitude=2.187, latitude=41.406, radius=1000
        ) == ["上海市"]
        assert await client.geosearch(
            "barcelona", longitude=2.191, latitude=41.433, height=1000, width=1000
        ) == ["place1"]
        assert await client.geosearch(
            "barcelona", member="place3", radius=100, unit="km"
        ) == [
            "上海市",
            "place1",
            "place3",
        ]
        # test count
        assert await client.geosearch(
            "barcelona", member="place3", radius=100, unit="km", count=2
        ) == ["place3", "上海市"]
        assert (
            await client.geosearch(
                "barcelona", member="place3", radius=100, unit="km", count=1, any=1
            )
        )[0] in ["place1", "place3", "上海市"]

    @pytest.mark.min_server_version("6.2.0")
    async def test_geosearch_member(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "上海市",
        )

        await client.geoadd("barcelona", *values)
        assert await client.geosearch("barcelona", member="place1", radius=4000) == [
            "上海市",
            "place1",
        ]
        assert await client.geosearch("barcelona", member="place1", radius=10) == [
            "place1"
        ]

        assert await client.geosearch(
            "barcelona",
            member="place1",
            radius=4000,
            withdist=True,
            withcoord=True,
            withhash=True,
        ) == [
            [
                "上海市",
                3067.4157,
                3471609625421029,
                (2.187376320362091, 41.40634178640635),
            ],
            [
                "place1",
                0.0,
                3471609698139488,
                (2.1909382939338684, 41.433790281840835),
            ],
        ]

    @pytest.mark.min_server_version("6.2.0")
    async def test_geosearch_sort(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )
        await client.geoadd("barcelona", *values)
        assert await client.geosearch(
            "barcelona", longitude=2.191, latitude=41.433, radius=3000, sort="ASC"
        ) == ["place1", "place2"]
        assert await client.geosearch(
            "barcelona", longitude=2.191, latitude=41.433, radius=3000, sort="DESC"
        ) == ["place2", "place1"]

    @pytest.mark.min_server_version("6.2.0")
    async def test_geosearch_with(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )
        await client.geoadd("barcelona", *values)

        # test a bunch of combinations to test the parse response
        # function.
        assert await client.geosearch(
            "barcelona",
            longitude=2.191,
            latitude=41.433,
            radius=1,
            unit="km",
            withdist=True,
            withcoord=True,
            withhash=True,
        ) == [
            [
                "place1",
                0.0881,
                3471609698139488,
                (2.19093829393386841, 41.43379028184083523),
            ]
        ]
        assert (
            await client.geosearch(
                "barcelona",
                longitude=2.191,
                latitude=41.433,
                radius=1,
                unit="km",
                withdist=True,
                withcoord=True,
            )
            == [["place1", 0.0881, (2.19093829393386841, 41.43379028184083523)]]
        )
        assert await client.geosearch(
            "barcelona",
            longitude=2.191,
            latitude=41.433,
            radius=1,
            unit="km",
            withhash=True,
            withcoord=True,
        ) == [
            [
                "place1",
                3471609698139488,
                (2.19093829393386841, 41.43379028184083523),
            ]
        ]
        # test no values.
        assert (
            await client.geosearch(
                "barcelona",
                longitude=2,
                latitude=1,
                radius=1,
                unit="km",
                withdist=True,
                withcoord=True,
                withhash=True,
            )
            == []
        )

    @pytest.mark.min_server_version("6.2.0")
    async def test_geosearch_negative(self, client):
        # not specifying member nor longitude and latitude
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona")
        # specifying member and longitude and latitude
        with pytest.raises(DataError):
            assert await client.geosearch(
                "barcelona", member="Paris", longitude=2, latitude=1
            )
        # specifying one of longitude and latitude
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona", longitude=2)
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona", latitude=2)

        # not specifying radius nor width and height
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona", member="Paris")
        # specifying radius and width and height
        with pytest.raises(DataError):
            assert await client.geosearch(
                "barcelona", member="Paris", radius=3, width=2, height=1
            )
        # specifying one of width and height
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona", member="Paris", width=2)
        with pytest.raises(DataError):
            assert await client.geosearch("barcelona", member="Paris", height=2)

        # invalid sort
        with pytest.raises(DataError):
            assert await client.geosearch(
                "barcelona", member="Paris", width=2, height=2, sort="wrong"
            )

        # invalid unit
        with pytest.raises(DataError):
            assert await client.geosearch(
                "barcelona", member="Paris", width=2, height=2, unit="miles"
            )

        # use any without count
        with pytest.raises(DataError):
            assert await client.geosearch(
                "barcelona", member="place3", radius=100, any=1
            )

    @pytest.mark.min_server_version("6.2.0")
    @pytest.mark.nocluster
    async def test_geosearchstore(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        await client.geosearchstore(
            "places_barcelona",
            "barcelona",
            longitude=2.191,
            latitude=41.433,
            radius=1000,
        )
        assert await client.zrange("places_barcelona", 0, -1) == [b"place1"]

    @pytest.mark.min_server_version("6.2.0")
    @pytest.mark.nocluster
    async def test_geosearchstore_dist(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        await client.geosearchstore(
            "places_barcelona",
            "barcelona",
            longitude=2.191,
            latitude=41.433,
            radius=1000,
            storedist=True,
        )
        # instead of save the geo score, the distance is saved.
        assert await client.zscore("places_barcelona", "place1") == 88.05060698409301

    async def test_georadius(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadius("barcelona", 2.191, 41.433, 1000) == ["place1"]

    async def test_georadius_no_values(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadius("barcelona", 1, 2, 1000) == []

    async def test_georadius_units(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadius("barcelona", 2.191, 41.433, 1, unit="km") == [
            "place1"
        ]

    async def test_georadius_with(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)

        # test a bunch of combinations to test the parse response
        # function.
        assert await client.georadius(
            "barcelona",
            2.191,
            41.433,
            1,
            unit="km",
            withdist=True,
            withcoord=True,
            withhash=True,
        ) == [
            [
                "place1",
                0.0881,
                3471609698139488,
                (2.19093829393386841, 41.43379028184083523),
            ]
        ]

        assert await client.georadius(
            "barcelona", 2.191, 41.433, 1, unit="km", withdist=True, withcoord=True
        ) == [["place1", 0.0881, (2.19093829393386841, 41.43379028184083523)]]

        assert await client.georadius(
            "barcelona", 2.191, 41.433, 1, unit="km", withhash=True, withcoord=True
        ) == [["place1", 3471609698139488, (2.19093829393386841, 41.43379028184083523)]]

        # test no values.
        assert (
            await client.georadius(
                "barcelona",
                2,
                1,
                1,
                unit="km",
                withdist=True,
                withcoord=True,
                withhash=True,
            )
            == []
        )

    async def test_georadius_count(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadius("barcelona", 2.191, 41.433, 3000, count=1) == [
            "place1"
        ]

    async def test_georadius_sort(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadius("barcelona", 2.191, 41.433, 3000, sort="ASC") == [
            "place1",
            "place2",
        ]
        assert await client.georadius(
            "barcelona", 2.191, 41.433, 3000, sort="DESC"
        ) == [
            "place2",
            "place1",
        ]

    @pytest.mark.nocluster
    async def test_georadius_store(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        await client.georadius(
            "barcelona", 2.191, 41.433, 1000, store="places_barcelona"
        )
        assert await client.zrange("places_barcelona", 0, -1) == [b"place1"]

    @pytest.mark.nocluster
    async def test_georadius_store_dist(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        await client.georadius(
            "barcelona", 2.191, 41.433, 1000, store_dist="places_barcelona"
        )
        # instead of save the geo score, the distance is saved.
        assert await client.zscore("places_barcelona", "place1") == 88.05060698409301

    async def test_georadiusmember(self, client):
        values = (2.1909389952632, 41.433791470673, "place1") + (
            2.1873744593677,
            41.406342043777,
            "place2",
        )

        await client.geoadd("barcelona", *values)
        assert await client.georadiusbymember("barcelona", "place1", 4000) == [
            "place2",
            "place1",
        ]
        assert await client.georadiusbymember("barcelona", "place1", 10) == ["place1"]

        assert await client.georadiusbymember(
            "barcelona", "place1", 4000, withdist=True, withcoord=True, withhash=True
        ) == [
            [
                "place2",
                3067.4157,
                3471609625421029,
                (2.187376320362091, 41.40634178640635),
            ],
            ["place1", 0.0, 3471609698139488, (2.1909382939338684, 41.433790281840835)],
        ]
