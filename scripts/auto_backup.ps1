# 自动化备份脚本（Windows PowerShell）
# 定期备份数据库、Redis和静态资源

$ErrorActionPreference = "Stop"

# 配置
$backupDir = "C:\backups"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$retentionDays = 30

# 创建备份目录
New-Item -ItemType Directory -Force -Path "$backupDir\db" | Out-Null
New-Item -ItemType Directory -Force -Path "$backupDir\redis" | Out-Null
New-Item -ItemType Directory -Force -Path "$backupDir\static" | Out-Null

# 数据库备份
Write-Host "[$(Get-Date)] Starting database backup..."
if ($env:DATABASE_URL -like "*postgresql*") {
    # PostgreSQL备份
    $backupFile = "$backupDir\db\postgres_$timestamp.sql"
    & pg_dump $env:DATABASE_URL -f $backupFile
    Write-Host "[$(Get-Date)] PostgreSQL backup completed: postgres_$timestamp.sql"
} elseif ($env:DATABASE_URL -like "*sqlite*") {
    # SQLite备份
    $dbPath = $env:DATABASE_URL -replace ".*:///", ""
    $backupFile = "$backupDir\db\sqlite_$timestamp.db"
    Copy-Item $dbPath $backupFile
    Write-Host "[$(Get-Date)] SQLite backup completed: sqlite_$timestamp.db"
}

# Redis备份
Write-Host "[$(Get-Date)] Starting Redis backup..."
if ($env:REDIS_URL) {
    redis-cli -u $env:REDIS_URL BGSAVE
    redis-cli -u $env:REDIS_URL LASTSAVE
    Write-Host "[$(Get-Date)] Redis backup completed"
}

# 清理过期备份
Write-Host "[$(Get-Date)] Cleaning old backups..."
$cutoffDate = (Get-Date).AddDays(-$retentionDays)
Get-ChildItem -Path "$backupDir" -Recurse -File | Where-Object {
    $_.LastWriteTime -lt $cutoffDate
} | Remove-Item -Force
Write-Host "[$(Get-Date)] Old backups cleaned"

Write-Host "[$(Get-Date)] Backup completed successfully"
