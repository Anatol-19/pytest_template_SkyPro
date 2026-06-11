$cmds = @(
    "python -m services.lighthouse.run --crux VRP_PROD main mobile",
    "python -m services.lighthouse.run --crux VRP_PROD s_video desktop",
    "python -m services.lighthouse.run --crux VRP_PROD s_video mobile",
    "python -m services.lighthouse.run --crux VRP_PROD models desktop",
    "python -m services.lighthouse.run --crux VRP_PROD models mobile",
    "python -m services.lighthouse.run --crux VRP_PROD s_model desktop",
    "python -m services.lighthouse.run --crux VRP_PROD s_model mobile",
    "python -m services.lighthouse.run --crux VRP_PROD categories desktop",
    "python -m services.lighthouse.run --crux VRP_PROD categories mobile",
    "python -m services.lighthouse.run --crux VRP_PROD s_category desktop",
    "python -m services.lighthouse.run --crux VRP_PROD s_category mobile",
    "python -m services.lighthouse.run --crux VRP_PROD s_studio desktop",
    "python -m services.lighthouse.run --crux VRP_PROD s_studio mobile",
    "python -m services.lighthouse.run --crux VRP_PROD dreams desktop",
    "python -m services.lighthouse.run --crux VRP_PROD dreams mobile",
    "python -m services.lighthouse.run --crux VRP_PROD s_dream desktop",
    "python -m services.lighthouse.run --crux VRP_PROD s_dream mobile",
    "python -m services.lighthouse.run --crux VRS_PROD main desktop",
    "python -m services.lighthouse.run --crux VRS_PROD main mobile",
    "python -m services.lighthouse.run --crux VRS_PROD s_video desktop",
    "python -m services.lighthouse.run --crux VRS_PROD s_video mobile",
    "python -m services.lighthouse.run --crux VRS_PROD models desktop",
    "python -m services.lighthouse.run --crux VRS_PROD models mobile",
    "python -m services.lighthouse.run --crux VRS_PROD s_model desktop",
    "python -m services.lighthouse.run --crux VRS_PROD s_model mobile",
    "python -m services.lighthouse.run --crux VRS_PROD categories desktop",
    "python -m services.lighthouse.run --crux VRS_PROD categories mobile",
    "python -m services.lighthouse.run --crux VRS_PROD s_category desktop",
    "python -m services.lighthouse.run --crux VRS_PROD s_category mobile",
    "python -m services.lighthouse.run --crux VRS_PROD s_studio desktop",
    "python -m services.lighthouse.run --crux VRS_PROD s_studio mobile",
    "python -m services.lighthouse.run --crux VRS_PROD dreams desktop",
    "python -m services.lighthouse.run --crux VRS_PROD dreams mobile",
    "python -m services.lighthouse.run --crux VRS_PROD s_dream desktop",
    "python -m services.lighthouse.run --crux VRS_PROD s_dream mobile"
)

foreach ($c in $cmds) {
    Write-Host "Running: $c"
    Invoke-Expression $c
}

Write-Host "DONE - All CrUX complete"