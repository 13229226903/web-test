$dir = "D:\Test\web-test\reports\allure-report-regression-3001"
$p = Start-Process -FilePath "python" -ArgumentList @("-m","http.server","8125","--bind","127.0.0.1") -WorkingDirectory $dir -WindowStyle Hidden -PassThru
$p.Id | Out-File "D:\Test\web-test\artifacts\2026-11-09_stable_regression_3001\allure_server.pid" -Encoding ascii
Write-Output "PID=$($p.Id)"
