"""x-client-transaction-id generator (stdlib only, no third-party deps).

Generates the per-request anti-bot token X's web client attaches to API calls.
Valid tokens REQUIRE the key + animation frames from the *logged-in* homepage
(https://x.com/home fetched with session cookies) - the logged-out page yields
tokens the server rejects.

Algorithm ported from twikit's twikit/x_client_transaction (MIT, by twikit
contributors) with BeautifulSoup replaced by regex + urllib so this file has
zero dependencies. Tested live 2026-09-19: tokens accepted (200) on
txn-gated endpoints (CreateTweet, users/show, account/settings, ...).

Key-byte indices [47, 41, 13, 12] were extracted 2026-09-19 from
abs.twimg.com/.../ondemand.s.0cc29d94ce9e97eea.js with the regex below.
If X rotates the deploy and tokens start failing, re-derive:
  1. DevTools Network tab -> find ondemand.s.<hash>a.js -> download it
  2. indices = re.findall(r"\\(\\w\\[(\\d{1,2})\\],\\s*16\\)", src)
  3. row_index, key_indices = indices[0], indices[1:]
"""
import base64
import hashlib
import math
import random
import re
import time
import urllib.request
from functools import reduce
from typing import List, Union

INDICES_REGEX = re.compile(r"(\(\w{1}\[(\d{1,2})\],\s*16\))+")

# ---------------------------------------------------------------- cubic ---
class Cubic:
    def __init__(self, curves: List[Union[float, int]]):
        self.curves = curves

    def get_value(self, time_: Union[float, int]):
        start_gradient = end_gradient = start = mid = 0.0
        end = 1.0
        if time_ <= 0.0:
            if self.curves[0] > 0.0:
                start_gradient = self.curves[1] / self.curves[0]
            elif self.curves[1] == 0.0 and self.curves[2] > 0.0:
                start_gradient = self.curves[3] / self.curves[2]
            return start_gradient * time_
        if time_ >= 1.0:
            if self.curves[2] < 1.0:
                end_gradient = (self.curves[3] - 1.0) / (self.curves[2] - 1.0)
            elif self.curves[2] == 1.0 and self.curves[0] < 1.0:
                end_gradient = (self.curves[1] - 1.0) / (self.curves[0] - 1.0)
            return 1.0 + end_gradient * (time_ - 1.0)
        while start < end:
            mid = (start + end) / 2
            x_est = self.calculate(self.curves[0], self.curves[2], mid)
            if abs(time_ - x_est) < 0.00001:
                return self.calculate(self.curves[1], self.curves[3], mid)
            if x_est < time_:
                start = mid
            else:
                end = mid
        return self.calculate(self.curves[1], self.curves[3], mid)

    @staticmethod
    def calculate(a, b, m):
        return 3.0 * a * (1 - m) * (1 - m) * m + 3.0 * b * (1 - m) * m * m + m * m * m


# ---------------------------------------------------------- interpolate ---
def _interpolate_num(from_val, to_val, f):
    if all(isinstance(n, (int, float)) for n in (from_val, to_val)):
        return from_val * (1 - f) + to_val * f
    if all(isinstance(n, bool) for n in (from_val, to_val)):
        return from_val if f < 0.5 else to_val


def interpolate(from_list, to_list, f):
    if len(from_list) != len(to_list):
        raise Exception(f"Mismatched interpolation arguments {from_list}: {to_list}")
    return [_interpolate_num(a, b, f) for a, b in zip(from_list, to_list)]


# ------------------------------------------------------------- rotation ---
def convert_rotation_to_matrix(rotation: Union[float, int]):
    rad = math.radians(rotation)
    return [math.cos(rad), -math.sin(rad), math.sin(rad), math.cos(rad)]


# ---------------------------------------------------------------- utils ---
def float_to_hex(x):
    result = []
    quotient = int(x)
    fraction = x - quotient
    while quotient > 0:
        quotient = int(x / 16)
        remainder = int(x - (float(quotient) * 16))
        result.insert(0, chr(remainder + 55) if remainder > 9 else str(remainder))
        x = float(quotient)
    if fraction == 0:
        return ''.join(result)
    result.append('.')
    while fraction > 0:
        fraction *= 16
        integer = int(fraction)
        fraction -= float(integer)
        result.append(chr(integer + 55) if integer > 9 else str(integer))
    return ''.join(result)


def is_odd(num: Union[int, float]):
    return -1.0 if num % 2 else 0.0


def base64_encode(data) -> str:
    data = data.encode() if isinstance(data, str) else data
    return base64.b64encode(data).decode()


# ---------------------------------------------------- transaction (sync) ---
class ClientTransaction:
    ADDITIONAL_RANDOM_NUMBER = 3
    DEFAULT_KEYWORD = "obfiowerehiring"

    def __init__(self, row_index: int = 47, key_indices=(41, 13, 12)):
        self.home_html = None
        self.frames_d = []
        self.key = None
        self.key_bytes = None
        self.animation_key = None
        self.row_index = row_index
        self.key_indices = list(key_indices)

    # -- stdlib replacements for the BeautifulSoup parts -------------------
    @staticmethod
    def extract_key(html: str) -> str:
        m = re.search(r'<meta[^>]*twitter-site-verification[^>]*content="([^"]+)"', html)
        if not m:
            m = re.search(r'<meta[^>]*content="([^"]+)"[^>]*twitter-site-verification', html)
        if not m:
            raise Exception("Couldn't get key from the page source")
        return m.group(1)

    @staticmethod
    def extract_frames(html: str) -> List[str]:
        """Return the animation-path `d` attr (2nd <path>) of each loading-x-anim svg."""
        ds = []
        for i in range(4):
            m = re.search(r'id="loading-x-anim-%d".*?</svg>' % i, html, re.S)
            if not m:
                raise Exception(f"loading-x-anim-{i} not found in page")
            paths = re.findall(r'<path[^>]*\sd="([^"]+)"', m.group(0))
            if len(paths) < 2:
                raise Exception(f"animation path missing in frame {i}")
            ds.append(paths[1])
        return ds

    def init_from_html(self, html: str):
        self.home_html = html
        self.key = self.extract_key(html)
        self.key_bytes = list(base64.b64decode(bytes(self.key, "utf-8")))
        self.frames_d = self.extract_frames(html)
        self.animation_key = self.get_animation_key(self.key_bytes)

    def init_logged_in(self, cookie: str, user_agent: str):
        req = urllib.request.Request(
            "https://x.com/home", headers={"User-Agent": user_agent, "Cookie": cookie})
        html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        self.init_from_html(html)

    # -- math (ported verbatim) --------------------------------------------
    def get_2d_array(self, key_bytes):
        d = self.frames_d[key_bytes[5] % 4]
        return [[int(x) for x in re.sub(r"[^\d]+", " ", item).strip().split()]
                for item in d[9:].split("C")]

    def solve(self, value, min_val, max_val, rounding: bool):
        result = value * (max_val - min_val) / 255 + min_val
        return math.floor(result) if rounding else round(result, 2)

    def animate(self, frames, target_time):
        from_color = [float(i) for i in [*frames[:3], 1]]
        to_color = [float(i) for i in [*frames[3:6], 1]]
        from_rotation = [0.0]
        to_rotation = [self.solve(float(frames[6]), 60.0, 360.0, True)]
        frames = frames[7:]
        curves = [self.solve(float(item), is_odd(c), 1.0, False)
                  for c, item in enumerate(frames)]
        val = Cubic(curves).get_value(target_time)
        color = [v if v > 0 else 0 for v in interpolate(from_color, to_color, val)]
        rotation = interpolate(from_rotation, to_rotation, val)
        matrix = convert_rotation_to_matrix(rotation[0])
        str_arr = [format(round(v), "x") for v in color[:-1]]
        for value in matrix:
            rounded = round(value, 2)
            if rounded < 0:
                rounded = -rounded
            hv = float_to_hex(rounded)
            str_arr.append(f"0{hv}".lower() if hv.startswith(".") else hv if hv else "0")
        str_arr.extend(["0", "0"])
        return re.sub(r"[.-]", "", "".join(str_arr))

    def get_animation_key(self, key_bytes):
        row_index = key_bytes[self.row_index] % 16
        frame_time = reduce(lambda a, b: a * b,
                            [key_bytes[i] % 16 for i in self.key_indices])
        frame_row = self.get_2d_array(key_bytes)[row_index]
        return self.animate(frame_row, float(frame_time) / 4096)

    def generate_transaction_id(self, method: str, path: str, time_now=None) -> str:
        time_now = time_now or math.floor((time.time() * 1000 - 1682924400 * 1000) / 1000)
        time_now_bytes = [(time_now >> (i * 8)) & 0xFF for i in range(4)]
        key_bytes = self.key_bytes or list(base64.b64decode(bytes(self.key, "utf-8")))
        animation_key = self.animation_key or self.get_animation_key(key_bytes)
        digest = hashlib.sha256(
            f"{method}!{path}!{time_now}{self.DEFAULT_KEYWORD}{animation_key}".encode()
        ).digest()
        random_num = random.randint(0, 255)
        arr = [*key_bytes, *time_now_bytes, *list(digest)[:16],
               self.ADDITIONAL_RANDOM_NUMBER]
        out = bytearray([random_num, *[b ^ random_num for b in arr]])
        return base64_encode(out).strip("=")


if __name__ == "__main__":
    print("import this module; see common.py for usage")
