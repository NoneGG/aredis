### WITH ASYNCIO ONLY:
Namespace(P=1, n=100000, s=2)
set_str - 100000 Requests
Duration  = 8.769839000000001
Rate = 11402.717883418383

set_int - 100000 Requests
Duration  = 8.73056
Rate = 11454.01898618187

get_str - 100000 Requests
Duration  = 8.221882
Rate = 12162.66543353456

get_int - 100000 Requests
Duration  = 8.255223
Rate = 12113.543147168766

incr - 100000 Requests
Duration  = 8.629779999999997
Rate = 11587.78091677888

lpush - 100000 Requests
Duration  = 8.830542999999999
Rate = 11324.331923869237

lrange_300 - 100000 Requests
Duration  = 10.162092999999999
Rate = 9840.492504841277

lpop - 100000 Requests
Duration  = 8.069283000000006
Rate = 12392.674789073568

hmset - 100000 Requests
Duration  = 10.295702000000006
Rate = 9712.790832524091

### WITH UVLOOP:
Namespace(P=1, n=100000, s=2)
set_str - 100000 Requests
Duration  = 5.342845999999994
Rate = 18716.61657476186

set_int - 100000 Requests
Duration  = 5.323021999999995
Rate = 18786.32100336991

get_str - 100000 Requests
Duration  = 4.892493999999999
Rate = 20439.473201193505

get_int - 100000 Requests
Duration  = 4.853779000000003
Rate = 20602.50373986948

incr - 100000 Requests
Duration  = 5.266047
Rate = 18989.576052017765

lpush - 100000 Requests
Duration  = 5.473873000000012
Rate = 18268.600678166957

lrange_300 - 100000 Requests
Duration  = 6.815705000000008
Rate = 14671.996513933611

lpop - 100000 Requests
Duration  = 4.892919000000006
Rate = 20437.69782414135

hmset - 100000 Requests
Duration  = 6.993429999999989
Rate = 14299.13504532113