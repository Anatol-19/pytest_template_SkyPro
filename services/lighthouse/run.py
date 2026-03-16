"""
CLI-обёртка для запуска Lighthouse тестов.

Использование:
    python -m services.lighthouse.run <environment> <route> <device> [iterations]

Примеры:
    python -m services.lighthouse.run VRS_DEV home desktop 10
    python -m services.lighthouse.run VRP_PROD home,login mobile 5
    python -m services.lighthouse.run VRS_TEST home desktop

Доступные environment: VRS_DEV, VRS_TEST, VRS_STAGE, VRS_PROD,
                       VRP_DEV, VRP_TEST, VRP_STAGE, VRP_PROD

Роуты берутся из URLs/routes.ini. Несколько роутов через запятую.
"""

import argparse
import configparser
import os
import sys

# Корень проекта
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "config_lighthouse.env")
load_dotenv(dotenv_path, override=True)

import services.lighthouse.configs.config_lighthouse as cfg

VALID_ENVIRONMENTS = [
    "VRS_DEV", "VRS_TEST", "VRS_STAGE", "VRS_PROD",
    "VRP_DEV", "VRP_TEST", "VRP_STAGE", "VRP_PROD",
]


def switch_environment(environment: str) -> str:
    """Переключает контур и возвращает base_url."""
    config = configparser.ConfigParser()
    config.read(cfg.CONFIG_PATH, encoding="utf-8")

    if environment not in config:
        print(f"[ERROR] Контур '{environment}' не найден в base_urls.ini")
        print(f"Доступные: {', '.join(VALID_ENVIRONMENTS)}")
        sys.exit(1)

    config["environments"]["current"] = environment
    with open(cfg.CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f)

    cfg.BASE_URL = None
    base_url = cfg.get_base_url()
    print(f"[OK] Контур: {environment} ({base_url})")
    return base_url


def main():
    parser = argparse.ArgumentParser(
        description="Запуск Lighthouse CLI тестов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Примеры:
  python -m services.lighthouse.run VRS_DEV home desktop 10
  python -m services.lighthouse.run VRP_PROD home,login mobile 5
  python -m services.lighthouse.run VRS_TEST home desktop
  python -m services.lighthouse.run --crux VRP_PROD home desktop""",
    )
    parser.add_argument("environment", choices=VALID_ENVIRONMENTS,
                        help="Контур (VRS_DEV, VRP_PROD и т.д.)")
    parser.add_argument("route", help="Роут или роуты через запятую (home, login, home,login)")
    parser.add_argument("device", choices=["desktop", "mobile"],
                        help="Тип устройства")
    parser.add_argument("iterations", nargs="?", type=int, default=10,
                        help="Количество итераций (по умолчанию 10)")
    parser.add_argument("--crux", action="store_true",
                        help="Собрать CrUX данные вместо CLI прогона")

    args = parser.parse_args()
    routes = [r.strip() for r in args.route.split(",")]

    base_url = switch_environment(args.environment)

    from services.lighthouse.pagespeed_service import SpeedtestService
    service = SpeedtestService(environment=args.environment)

    if args.crux:
        print(f"[START] CrUX: {', '.join(routes)} | {args.device}")
        service.run_crux_data_collection(
            route_keys=routes,
            device_type=args.device,
            base_url=base_url,
        )
    else:
        print(f"[START] Lighthouse CLI: {', '.join(routes)} | {args.device} | {args.iterations} итераций")
        service.run_local_tests(
            route_keys=routes,
            device_type=args.device,
            n_iteration=args.iterations,
            base_url=base_url,
        )

    print(f"[DONE] Результаты записаны в Google Sheets.")


if __name__ == "__main__":
    main()
