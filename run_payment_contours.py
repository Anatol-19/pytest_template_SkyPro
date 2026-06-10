"""Последовательный прогон payment-тестов по нескольким VRP-контурам.

Пример:
    python run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE
    python run_payment_contours.py --contours VRP_STAGE -k TestTariffs

PROD не входит в дефолт — добавляется только явно.
"""

import argparse
import subprocess
import sys

from services.payment.config_payment import DEFAULT_CONTOURS


def main():
    parser = argparse.ArgumentParser(description="Прогон payment-тестов по контурам VRP")
    parser.add_argument("--contours", default=",".join(DEFAULT_CONTOURS),
                        help="Список контуров через запятую (default: %(default)s)")
    parser.add_argument("-k", dest="keyword", default=None, help="Фильтр pytest -k")
    parser.add_argument("--pay-category", default="")
    parser.add_argument("--pay-tab", default="monthly")
    args, extra = parser.parse_known_args()

    contours = [c.strip() for c in args.contours.split(",") if c.strip()]
    results = {}
    for env in contours:
        print(f"\n{'=' * 60}\n▶ Контур: {env}\n{'=' * 60}")
        cmd = [sys.executable, "-m", "pytest", "-m", "payment",
               f"--environment={env}", f"--pay-category={args.pay_category}",
               f"--pay-tab={args.pay_tab}", "-v"]
        if args.keyword:
            cmd += ["-k", args.keyword]
        cmd += extra
        results[env] = subprocess.run(cmd).returncode

    print(f"\n{'=' * 60}\nИтог по контурам:")
    for env, code in results.items():
        print(f"  {env}: {'OK' if code == 0 else f'FAILED (код {code})'}")
    sys.exit(0 if all(c == 0 for c in results.values()) else 1)


if __name__ == "__main__":
    main()
