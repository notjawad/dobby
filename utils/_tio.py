import zlib
import aiohttp
import re

from functools import partial

to_bytes = partial(bytes, encoding="utf-8")


def to_tio_string(pair):
    name, obj = pair

    # Directly return if the object is falsy (empty or None)
    if not obj:
        return b""

    if isinstance(obj, list):
        content = (
            str(item)
            for sublist in ([f"V{name}", str(len(obj))], obj)
            for item in sublist
        )
    else:
        content = [f"F{name}", str(len(to_bytes(obj))), obj]

    return to_bytes("\x00".join(content) + "\x00")


class Tio:
    def __init__(
        self,
        language: str,
        code: str,
        inputs="",
        compilerFlags=None,
        commandLineOptions=None,
        args=None,
    ):
        if compilerFlags is None:
            compilerFlags = []
        if commandLineOptions is None:
            commandLineOptions = []
        if args is None:
            args = []
        self.backend = "https://tio.run/cgi-bin/run/api/"

        strings = {
            "lang": [language],
            ".code.tio": code,
            ".input.tio": inputs,
            "TIO_CFLAGS": compilerFlags,
            "TIO_OPTIONS": commandLineOptions,
            "args": args,
        }

        bytes_ = (
            b"".join(map(to_tio_string, zip(strings.keys(), strings.values()))) + b"R"
        )

        self.request = zlib.compress(bytes_, 9)[2:-4]

    async def send(self):
        async with aiohttp.ClientSession(
            headers={"Connection": "keep-alive"}
        ) as client_session:
            async with client_session.post(self.backend, data=self.request) as res:
                if res.status != 200:
                    raise aiohttp.HttpProcessingError(res.status)

                data = await res.read()
                data = data.decode("utf-8")
                return data.replace(data[:16], "")

    def parse_metrics(self, output: str) -> dict:
        metrics = {}
        patterns = {
            "real_time": r"Real time: ([\d.]+) s",
            "user_time": r"User time: ([\d.]+) s",
            "sys_time": r"Sys\. time: ([\d.]+) s",
            "exit_code": r"Exit code: (\d+)",
        }

        for key, pattern in patterns.items():
            if match := re.search(pattern, output):
                metrics[key] = match[1]

        return metrics
