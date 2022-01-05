from coredis.exceptions import RedisError
from coredis.utils import b, nativestr


def parse_georadius_generic(response, **options):
    if options["store"] or options["store_dist"]:
        # `store` and `store_diff` cant be combined
        # with other command arguments.
        return response

    if type(response) != list:
        response_list = [response]
    else:
        response_list = response

    if not options["withdist"] and not options["withcoord"] and not options["withhash"]:
        # just a bunch of places
        return [nativestr(r) for r in response_list]

    cast = {
        "withdist": float,
        "withcoord": lambda ll: (float(ll[0]), float(ll[1])),
        "withhash": int,
    }

    # zip all output results with each casting functino to get
    # the properly native Python value.
    f = [nativestr]
    f += [cast[o] for o in ["withdist", "withhash", "withcoord"] if options[o]]
    return [list(map(lambda fv: fv[0](fv[1]), zip(f, r))) for r in response_list]


class GeoCommandMixin:

    RESPONSE_CALLBACKS = {
        "GEOPOS": lambda r: list(
            map(lambda ll: (float(ll[0]), float(ll[1])) if ll is not None else None, r)
        ),
        "GEOHASH": lambda r: list(r),
        "GEORADIUS": parse_georadius_generic,
        "GEORADIUSBYMEMBER": parse_georadius_generic,
        "GEODIST": float,
        "GEOADD": int,
    }

    # GEO COMMANDS
    async def geoadd(self, name, *values):
        """
        Add the specified geospatial items to the specified key identified
        by the ``name`` argument. The Geospatial items are given as ordered
        members of the ``values`` argument, each item or place is formed by
        the triad latitude, longitude and name.
        """
        if len(values) % 3 != 0:
            raise RedisError("GEOADD requires places with lon, lat and name" " values")
        return await self.execute_command("GEOADD", name, *values)

    async def geodist(self, name, place1, place2, unit=None):
        """
        Return the distance between ``place1`` and ``place2`` members of the
        ``name`` key.
        The units must be one of the following : m, km mi, ft. By async default
        meters are used.
        """
        pieces = [name, place1, place2]
        if unit and unit not in ("m", "km", "mi", "ft"):
            raise RedisError("GEODIST invalid unit")
        elif unit:
            pieces.append(unit)
        return await self.execute_command("GEODIST", *pieces)

    async def geohash(self, name, *values):
        """
        Return the geo hash string for each item of ``values`` members of
        the specified key identified by the ``name``argument.
        """
        return await self.execute_command("GEOHASH", name, *values)

    async def geopos(self, name, *values):
        """
        Return the positions of each item of ``values`` as members of
        the specified key identified by the ``name``argument. Each position
        is represented by the pairs lon and lat.
        """
        return await self.execute_command("GEOPOS", name, *values)

    async def georadius(
        self,
        name,
        longitude,
        latitude,
        radius,
        unit=None,
        withdist=False,
        withcoord=False,
        withhash=False,
        count=None,
        sort=None,
        store=None,
        store_dist=None,
    ):
        """
        Return the members of the specified key identified by the
        ``name`` argument which are within the borders of the area specified
        with the ``latitude`` and ``longitude`` location and the maximum
        distance from the center specified by the ``radius`` value.

        The units must be one of the following : m, km mi, ft. By default

        ``withdist`` indicates to return the distances of each place.

        ``withcoord`` indicates to return the latitude and longitude of
        each place.

        ``withhash`` indicates to return the geohash string of each place.

        ``count`` indicates to return the number of elements up to N.

        ``sort`` indicates to return the places in a sorted way, ASC for
        nearest to fairest and DESC for fairest to nearest.

        ``store`` indicates to save the places names in a sorted set named
        with a specific key, each element of the destination sorted set is
        populated with the score got from the original geo sorted set.

        ``store_dist`` indicates to save the places names in a sorted set
        named with a specific key, instead of ``store`` the sorted set
        destination score is set with the distance.
        """
        return await self._georadiusgeneric(
            "GEORADIUS",
            name,
            longitude,
            latitude,
            radius,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
            withhash=withhash,
            count=count,
            sort=sort,
            store=store,
            store_dist=store_dist,
        )

    async def georadiusbymember(
        self,
        name,
        member,
        radius,
        unit=None,
        withdist=False,
        withcoord=False,
        withhash=False,
        count=None,
        sort=None,
        store=None,
        store_dist=None,
    ):
        """
        This command is exactly like ``georadius`` with the sole difference
        that instead of taking, as the center of the area to query, a longitude
        and latitude value, it takes the name of a member already existing
        inside the geospatial index represented by the sorted set.
        """
        return await self._georadiusgeneric(
            "GEORADIUSBYMEMBER",
            name,
            member,
            radius,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
            withhash=withhash,
            count=count,
            sort=sort,
            store=store,
            store_dist=store_dist,
        )

    async def _georadiusgeneric(self, command, *args, **kwargs):
        pieces = list(args)
        if kwargs["unit"] and kwargs["unit"] not in ("m", "km", "mi", "ft"):
            raise RedisError("GEORADIUS invalid unit")
        elif kwargs["unit"]:
            pieces.append(kwargs["unit"])
        else:
            pieces.append("m",)

        for token in ("withdist", "withcoord", "withhash"):
            if kwargs[token]:
                pieces.append(b(token.upper()))

        if kwargs["count"]:
            pieces.extend([b("COUNT"), kwargs["count"]])

        if kwargs["sort"] and kwargs["sort"] not in ("ASC", "DESC"):
            raise RedisError("GEORADIUS invalid sort")
        elif kwargs["sort"]:
            pieces.append(b(kwargs["sort"]))

        if kwargs["store"] and kwargs["store_dist"]:
            raise RedisError("GEORADIUS store and store_dist cant be set" " together")

        if kwargs["store"]:
            pieces.extend([b("STORE"), kwargs["store"]])

        if kwargs["store_dist"]:
            pieces.extend([b("STOREDIST"), kwargs["store_dist"]])

        return await self.execute_command(command, *pieces, **kwargs)
