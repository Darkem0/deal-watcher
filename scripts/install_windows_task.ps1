param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,
    [string]$TaskName = "DealWatcher",
    [switch]$AtStartup,
    [switch]$Force,
    [switch]$NoElevation,
    [switch]$Elevated
)

$ErrorActionPreference = "Stop"

try {
    $OutputEncoding = [System.Text.UTF8Encoding]::new()
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
} catch {
    # Windows PowerShell hosts may not expose a writable console encoding.
}

function Test-IsAdministrator {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [System.Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole(
        [System.Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

function Get-PowerShellExecutable {
    $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    if ($null -ne $pwsh) { return $pwsh.Source }
    $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($null -ne $powershell) { return $powershell.Source }
    throw "pwsh.exe veya powershell.exe bulunamadı."
}

function Invoke-SelfElevated {
    param([string]$ResolvedProjectRoot)

    $shell = Get-PowerShellExecutable
    $arguments = @(
        "-NoProfile"
        "-ExecutionPolicy", "Bypass"
        "-File", $PSCommandPath
        "-ProjectRoot", $ResolvedProjectRoot
        "-TaskName", $TaskName
        "-Elevated"
    )
    if ($AtStartup) { $arguments += "-AtStartup" }
    if ($Force) { $arguments += "-Force" }

    try {
        $child = Start-Process -FilePath $shell -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    } catch {
        Write-Error "Yönetici yetkisi istenemedi veya UAC isteği reddedildi. Görev kurulmadı."
        exit 1
    }
    if ($child.ExitCode -ne 0) {
        Write-Error "Yükseltilmiş görev kurulumu başarısız oldu. Exit code: $($child.ExitCode)"
    }
    exit $child.ExitCode
}

function Test-AccessDenied {
    param([System.Management.Automation.ErrorRecord]$ErrorRecord)
    $text = $ErrorRecord | Out-String
    return $text -match "0x80070005|Access is denied|Erişim engellendi|UnauthorizedAccess"
}

try {
    $resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
    $pyprojectPath = Join-Path $resolvedRoot "pyproject.toml"
    $pythonPath = Join-Path $resolvedRoot ".venv\Scripts\python.exe"
    $envPath = Join-Path $resolvedRoot ".env"
    $configPath = Join-Path $resolvedRoot "config"
    $logsPath = Join-Path $resolvedRoot "logs"

    if (-not (Test-Path -LiteralPath $pyprojectPath -PathType Leaf)) {
        throw "pyproject.toml bulunamadı: $pyprojectPath"
    }
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw ".venv Python bulunamadı: $pythonPath"
    }
    if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        throw ".env bulunamadı: $envPath"
    }
    if (-not (Test-Path -LiteralPath $configPath -PathType Container)) {
        throw "config klasörü bulunamadı: $configPath"
    }
    New-Item -ItemType Directory -Path $logsPath -Force | Out-Null

    Push-Location $resolvedRoot
    try {
        & $pythonPath -c "import deal_watcher.scheduler"
        if ($LASTEXITCODE -ne 0) { throw "Scheduler modülü import edilemedi." }
        & $pythonPath -m deal_watcher.cli validate-config
        if ($LASTEXITCODE -ne 0) {
            throw "Yapılandırma doğrulaması başarısız; görev kurulmadı."
        }
    } finally {
        Pop-Location
    }

    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $existing -and -not $Force) {
        throw "Görev '$TaskName' zaten var. Güncellemek için -Force kullanın."
    }

    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    $action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m deal_watcher.cli run" -WorkingDirectory $resolvedRoot
    $trigger = if ($AtStartup) {
        New-ScheduledTaskTrigger -AtStartup
    } else {
        New-ScheduledTaskTrigger -AtLogOn
    }
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

    try {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Deal Watcher forum monitor" -Force:$Force | Out-Null
    } catch {
        if ((Test-AccessDenied $_) -and -not $Elevated -and -not $NoElevation) {
            Invoke-SelfElevated -ResolvedProjectRoot $resolvedRoot
        }
        if ((Test-AccessDenied $_) -and $NoElevation) {
            throw "Görev kaydı için erişim reddedildi. -NoElevation kullanıldığı için UAC denenmedi."
        }
        throw
    }

    $registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    $registeredInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
    if ($null -eq $registered -or $null -eq $registeredInfo) {
        throw "Görev kaydedildi ancak doğrulanamadı."
    }

    Write-Host "Windows zamanlanmış görevi kuruldu."
    Write-Host ""
    Write-Host "Görev adı: $TaskName"
    Write-Host "Kullanıcı: $currentUser"
    Write-Host "Yetki düzeyi: Limited"
    Write-Host "Çalışma dizini: $resolvedRoot"
    Write-Host "Program: $pythonPath"
    Write-Host "Durum: $($registered.State)"
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
