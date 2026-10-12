param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [switch]$Check
)
$ErrorActionPreference = "Stop"
try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new()
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
} catch { }
try {
    $root = (Resolve-Path -LiteralPath $ProjectRoot).Path
    Set-Location -LiteralPath $root
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE ".local\bin\uv.exe" }
    if (-not (Test-Path -LiteralPath $uvPath -PathType Leaf)) {
        Write-Host "Python kurulumunu yöneten uv henüz kurulu değil."
        Write-Host "Resmi astral.sh yükleyicisi indirilecek; yönetici yetkisi gerekmez."
        $answer = Read-Host "uv kurulsun mu? [E/h]"
        if ($answer -match '^(h|n)$') { Write-Host "Kurulum iptal edildi."; exit 1 }
        $installer = Join-Path ([System.IO.Path]::GetTempPath()) ("deal-watcher-uv-" + [guid]::NewGuid() + ".ps1")
        $oldNoPath = $env:UV_NO_MODIFY_PATH
        try {
            $env:UV_NO_MODIFY_PATH = "1"
            Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -OutFile $installer -UseBasicParsing
            & $installer
        } finally {
            $env:UV_NO_MODIFY_PATH = $oldNoPath
            Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue
        }
        if (-not (Test-Path -LiteralPath $uvPath -PathType Leaf)) { throw "uv bulunamadı. docs/kurulum.md rehberine bakın." }
    }
    Write-Host "Python ve uygulama bağımlılıkları hazırlanıyor (ilk açılış biraz sürebilir)..."
    & $uvPath sync --locked --no-dev
    if ($LASTEXITCODE -ne 0) { throw "Bağımlılıklar kurulamadı. İnternet bağlantısını kontrol edin." }
    $pythonPath = Join-Path $root ".venv\Scripts\python.exe"
    if ($Check) { & $pythonPath -m deal_watcher.cli validate-config }
    else { & $pythonPath -m deal_watcher.launcher }
    exit $LASTEXITCODE
} catch {
    Write-Host "Başlatılamadı: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "docs/izinler-windows.md rehberine bakın."
    exit 1
}
