from services.lighthouse.pagespeed_service import SpeedtestService

DEVICES = ["desktop", "mobile"]


def run_cli_saturation(environment: str, tag: str):
    print(f"\n=== CLI saturation: {environment} ===")
    service = SpeedtestService(environment=environment)
    for device in DEVICES:
        run_tag = f"{tag}_{device}"
        print(f"-- {environment} ({device}): 10 итераций по всем роутам, тег {run_tag}")
        service.run_local_tests(route_keys=None, device_type=device, n_iteration=10, tag=run_tag)


def run_api_saturation(environment: str, tag: str):
    print(f"\n=== API saturation: {environment} ===")
    service = SpeedtestService(environment=environment)
    for device in DEVICES:
        run_tag = f"{tag}_{device}"
        print(f"-- {environment} API ({device}): 10 итераций по всем роутам, тег {run_tag}")
        service.run_api_aggregated_tests(route_keys=None, device_type=device, n_iteration=10, tag=run_tag)


if __name__ == "__main__":
    run_cli_saturation("VRP_STAGE", "vrp_stage_cli")
    run_cli_saturation("VRP_PROD", "vrp_prod_cli")
    run_api_saturation("VRP_PROD", "vrp_prod_api")
