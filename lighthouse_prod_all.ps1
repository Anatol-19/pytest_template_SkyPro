# Lighthouse PROD tests - all routes, all devices, 10 iterations
$routes = "main,models,categories,s_video,s_model,s_category,s_studio,dreams,s_dream"

Write-Host "🚀 VRP_PROD: все роуты, все устройства, 10 итераций"
Write-Host "⏱️ Ожидаемое время: ~40-50 минут"

# Desktop
Write-Host "🖥️ Desktop: 10 итераций"
python -m services.lighthouse.run VRP_PROD main,models,categories,s_video,s_model,s_category,s_studio,dreams,s_dream desktop 10

# Mobile  
Write-Host "📱 Mobile: 10 итераций"
python -m services.lighthouse.run VRP_PROD main,models,categories,s_video,s_model,s_category,s_studio,dreams,s_dream mobile 10

Write-Host "✅ PROD тесты завершены"