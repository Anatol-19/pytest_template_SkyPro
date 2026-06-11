import configparser
import os

import anyio
from fastmcp.client.client import Client

SERVER_URL = "http://127.0.0.1:8000/mcp"
ROUTES_PATH = os.path.join("services", "lighthouse", "configs", "routes.ini")


def _read_routes():
    parser = configparser.ConfigParser()
    parser.read(ROUTES_PATH, encoding="utf-8")
    if "routes" not in parser:
        raise SystemExit("routes.ini не содержит секцию [routes]")
    return list(parser["routes"].keys())


async def main():
    routes = _read_routes()
    targets = ["VRP_DEV", "VRP_STAGE"]
    devices = ["desktop", "mobile"]
    async with Client(SERVER_URL) as client:
        for env in targets:
            print(f"Запускаю сатурацию для {env} ({len(routes)} маршрутов) …")
            result = await client.call_tool(
                "enqueue_environment_saturation",
                {
                    "environment": env,
                    "routes": routes,
                    "devices": devices,
                    "iterations": 10,
                    "tag": f"saturation_{env.lower()}",
                },
            )
            print(result)


if __name__ == "__main__":
    anyio.run(main)
