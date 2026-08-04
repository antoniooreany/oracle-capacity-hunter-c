Write-Host "=== Толерантный запуск pytest на Windows ===`n"

try {
    # Запуск тестов так же, как в CI (с покрытием)
    pytest --cov=capacity_hunter --cov-report=xml --cov-report=term
    Write-Host "`npytest завершился, смотри выше вывод для реальных тестовых ошибок."
} catch {
    $msg = $_.Exception.ToString()

    if ($msg -like "*PermissionError: [WinError 5]*pytest-of-anton*pytest-current*") {
        Write-Host "`nПойман известный Windows PermissionError при очистке временной директории."
        Write-Host "Все тесты уже были выполнены до этой стадии; считаем прогон условно успешным для локальной разработки."
    } else {
        Write-Host "`npytest завершился с другой ошибкой (не WinError 5) — смотри детали ниже:"
        Write-Host $msg
        throw
    }
}
