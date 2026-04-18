"""
target.py -- reference payload for Nuitka library-code recovery.

The point is not what this program *does* at runtime; the point is what
Nuitka helpers end up compiled into the binary. BinDiff/Diaphora will
match functions structurally, so we want broad coverage of:

  * Common stdlib modules (hashing, sockets, ssl, json, re, subprocess...)
  * Nuitka's own runtime helpers: dict/list/tuple/set construction,
    f-string formatting, unpacking, slicing, exception machinery, with-
    statement, generators, coroutines, class construction with __slots__,
    comprehensions of every flavor.

Add more imports / patterns here if you know specific modules flake.exe
uses -- matches are always better with more neighbourhood evidence.
"""

import os, sys, io, json, re, struct, hashlib, base64, binascii
import socket, ssl, http.client, urllib.parse, urllib.request
import threading, queue, concurrent.futures, asyncio
import collections, itertools, functools, operator, contextlib
import email, email.parser, xml.etree.ElementTree as ET
import zipfile, gzip, bz2, lzma, tarfile
import sqlite3, pickle, marshal
import ctypes, ctypes.wintypes
import logging, argparse, subprocess, tempfile, shutil


class _Example:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return f"Example({self.x!r}, {self.y!r})"

    def __iter__(self):
        yield self.x
        yield self.y

    def __eq__(self, other):
        return isinstance(other, _Example) and (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))


def _gen(n):
    for i in range(n):
        yield i * i


async def _aio():
    async def inner(x):
        await asyncio.sleep(0)
        return x + 1

    results = []
    async for i in _aiter(3):
        results.append(await inner(i))
    return results


async def _aiter(n):
    for i in range(n):
        yield i


def _exercise_patterns():
    # dict/list/tuple/set comprehensions
    d = {i: str(i) for i in range(5)}
    l = [x for x in _gen(10)]
    t = tuple(d.items())
    s = {*l, *d.keys()}

    # f-strings, slicing, star-unpacking
    a, *mid, z = l
    head, tail = l[:3], l[-3:]
    msg = f"a={a}, mid={mid!r}, z={z}, head={head}, tail={tail}"

    # exception handling (try/except/else/finally + chaining)
    caught = None
    try:
        try:
            raise ValueError("boom")
        except ValueError as inner:
            raise RuntimeError("wrapped") from inner
    except RuntimeError as e:
        caught = f"{type(e).__name__}: {e} <- {type(e.__cause__).__name__}"
    finally:
        pass

    # context managers (with + ExitStack)
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.suppress(FileNotFoundError))
        stack.callback(lambda: None)

    # class + dataclass-like + hashing + bytes
    ex1, ex2 = _Example(1, 2), _Example(1, 2)
    same = ex1 == ex2 and hash(ex1) == hash(ex2)
    h = hashlib.sha256(msg.encode()).hexdigest()
    b = base64.b64encode(msg.encode())

    # json / re / struct / socket stuff (pulls in lots of helpers)
    j = json.loads(json.dumps({"list": l, "dict": d, "same": same}))
    m = re.match(r"(?P<k>\w+)=(?P<v>\d+)", "answer=42")
    packed = struct.pack(">IHB", 0xdeadbeef, 0x1234, 0x7f)

    return msg, caught, ex1, h, b, j, m.groupdict() if m else None, packed.hex()


def _exercise_threading():
    q = queue.Queue()
    def worker():
        for i in range(3):
            q.put(i)
    t = threading.Thread(target=worker)
    t.start()
    t.join()
    out = []
    while not q.empty():
        out.append(q.get())

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(pow, i, 2) for i in range(4)]
        out += [f.result() for f in futs]
    return out


def main():
    print("nuitka reference payload")
    for item in _exercise_patterns():
        print(" ", item)
    print("threading:", _exercise_threading())
    try:
        print("async:", asyncio.run(_aio()))
    except Exception as e:
        print("async failed:", e)


if __name__ == "__main__":
    main()
