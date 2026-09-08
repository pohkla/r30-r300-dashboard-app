[CmdletBinding(SupportsShouldProcess = $true)]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$source = 'D:\black\Project\R300\src'
$mql5Root = 'C:\Users\Phadungsak\AppData\Roaming\MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05\MQL5'
$expertsRoot = Join-Path $mql5Root 'Experts'
# R300_EA is one folder name; the underscore is literal, not a path separator.
$destination = 'C:\Users\Phadungsak\AppData\Roaming\MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05\MQL5\Experts\R300_EA'
$requiredFiles = @(
    'R300_EA.mq5',
    'R300_Config.mqh',
    'R300_Trend.mqh',
    'R300_Structure.mqh',
    'R300_Setup.mqh',
    'R300_Entry.mqh',
    'R300_Risk.mqh',
    'R300_Exit.mqh'
)

# Reject redirected directories before writing to the fixed MT5 location.
function Assert-NoReparsePoint {
    param([string]$Path)
    $current = [System.IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse point is not allowed: $current"
            }
        }
        $current = [System.IO.Path]::GetDirectoryName($current)
    }
}

try {
    # Require a single R300_EA folder directly below this terminal's Experts.
    if ((Split-Path -Path $destination -Leaf) -cne 'R300_EA' -or
        (Split-Path -Path $destination -Parent) -ine $expertsRoot -or
        $destination -match '\\MQL5\\MQL5\\') {
        throw "Invalid MT5 destination: $destination"
    }
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Source directory not found: $source"
    }
    foreach ($directory in @($mql5Root, $expertsRoot)) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            throw "MT5 directory not found: $directory. Check MT5 File > Open Data Folder."
        }
    }
    Assert-NoReparsePoint -Path $source
    Assert-NoReparsePoint -Path $destination
    if ((Test-Path -LiteralPath $destination) -and
        -not (Test-Path -LiteralPath $destination -PathType Container)) {
        throw "Destination is not a directory: $destination"
    }

    # Validate the complete allowlist before creating or copying anything.
    foreach ($name in $requiredFiles) {
        $sourceFile = Join-Path $source $name
        $targetFile = Join-Path $destination $name
        if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
            throw "Required source file not found: $sourceFile"
        }
        Assert-NoReparsePoint -Path $sourceFile
        Assert-NoReparsePoint -Path $targetFile
        if (Test-Path -LiteralPath $targetFile -PathType Container) {
            throw "Target file path is a directory: $targetFile"
        }
    }

    Write-Host "Source: $source"
    Write-Host "Destination: $destination"
    if ($PSCmdlet.ShouldProcess($destination, 'Create directory if needed and copy 8 source files')) {
        if (-not (Test-Path -LiteralPath $destination -PathType Container)) {
            New-Item -ItemType Directory -Path $destination | Out-Null
        }
        foreach ($name in $requiredFiles) {
            Copy-Item -LiteralPath (Join-Path $source $name) -Destination (Join-Path $destination $name) -Force
            Write-Host "Copied: $name"
        }
        Write-Host 'Deploy complete. Compile R300_EA.mq5 in MetaEditor.'
    }
}
catch {
    throw "R300 deploy failed: $($_.Exception.Message)"
}

