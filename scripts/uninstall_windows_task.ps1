param(
    [string]$TaskName = "DealWatcher",
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

function Get-PowerShellExecutable {
    $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    if ($null -ne $pwsh) { return $pwsh.Source }
    $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($null -ne $powershell) { return $powershell.Source }
    throw "pwsh.exe veya powershell.exe bulunamadı."
}

function Test-AccessDenied {
    param([System.Management.Automation.ErrorRecord]$ErrorRecord)
    $text = $ErrorRecord | Out-String
    return $text -match "0x80070005|Access is denied|Erişim engellendi|UnauthorizedAccess"
}

function Invoke-SelfElevated {
    $shell = Get-PowerShellExecutable
    $arguments = @(
        "-NoProfile"
        "-ExecutionPolicy", "Bypass"
        "-File", $PSCommandPath
        "-TaskName", $TaskName
        "-Elevated"
    )
    try {
        $child = Start-Process -FilePath $shell -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    } catch {
        Write-Error "Yönetici yetkisi istenemedi veya UAC isteği reddedildi. Görev kaldırılmadı."
        exit 1
    }
    if ($child.ExitCode -ne 0) {
        Write-Error "Yükseltilmiş görev kaldırma başarısız oldu. Exit code: $($child.ExitCode)"
    }
    exit $child.ExitCode
}

try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "Görev bulunamadı: $TaskName"
        exit 0
    }
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    } catch {
        if ((Test-AccessDenied $_) -and -not $Elevated -and -not $NoElevation) {
            Invoke-SelfElevated
        }
        if ((Test-AccessDenied $_) -and $NoElevation) {
            throw "Görev kaldırma için erişim reddedildi. -NoElevation kullanıldığı için UAC denenmedi."
        }
        throw
    }
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        throw "Görev kaldırma doğrulanamadı: $TaskName"
    }
    Write-Host "Görev kaldırıldı: $TaskName"
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
