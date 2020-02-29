"""
compat package is used for import compat between different python version
"""

try:
    from asyncio import CancelledError, TimeoutError
except ImportError:
    from asyncio.futures import CancelledError, TimeoutError
