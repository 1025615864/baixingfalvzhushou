@echo off
chcp 65001 >nul
echo === 前端模拟测试报告 === > frontend_test_report.txt
echo 测试时间: %date% %time% >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试1] 检查前端服务状态...
curl -s -o nul -w "HTTP状态码: %%{http_code}\n" http://localhost:3000 >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试2] 检查首页加载...
curl -s http://localhost:3000 | findstr /i "title" >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试3] 测试静态资源加载...
curl -s -o nul -w "index.html: %%{http_code}\n" http://localhost:3000/index.html >> frontend_test_report.txt
curl -s -o nul -w "manifest.json: %%{http_code}\n" http://localhost:3000/manifest.json >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试4] 测试API代理连接...
curl -s -o nul -w "API健康检查: %%{http_code}\n" http://localhost:3000/api/health 2>&1 >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试5] 检查常见路由页面...
for %%p in (/chat /forum /news /lawfirm /login) do (
    echo 路由 %%p: >> frontend_test_report.txt
    curl -s -o nul -w "HTTP %%{http_code}\n" http://localhost:3000%%p 2>&1 >> frontend_test_report.txt
)
echo. >> frontend_test_report.txt

echo [测试6] 性能测试...
echo 首页加载时间测试: >> frontend_test_report.txt
powershell -Command "$time = Measure-Command { (curl -s http://localhost:3000 | Out-Null) }; Write-Output \"加载时间: $($time.TotalMilliseconds)ms\"" >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试7] 错误处理测试...
echo 不存在的页面404测试: >> frontend_test_report.txt
curl -s -o nul -w "404页面: %%{http_code}\n" http://localhost:3000/nonexistent 2>&1 >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo [测试8] HTTP头部检查...
echo 安全头部检查: >> frontend_test_report.txt
curl -s -I http://localhost:3000 | findstr /i "security content-type" >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo === 测试完成 === >> frontend_test_report.txt
echo. >> frontend_test_report.txt

echo 查看完整测试结果: type frontend_test_report.txt
type frontend_test_report.txt