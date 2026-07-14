# mirror-memory-to-obsidian.ps1  (Template — Platzhalter werden vom Setup ersetzt)
# PostToolUse-Hook (Matcher Write|Edit): Wenn Claude eine Memory-.md-Datei
# schreibt/bearbeitet, wird sie 1:1 in den Obsidian-Vault gespiegelt.
# Liest das Hook-JSON von stdin, prueft tool_input.file_path und kopiert bei
# Treffern. Blockiert nie: Exit-Code ist immer 0.

$memDir = '__MEMORY_DIR__'
$vault  = '__VAULT_DIR__'

try {
    if (-not [Console]::IsInputRedirected) { exit 0 }
    $raw = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $data = $raw | ConvertFrom-Json
    $fp = $data.tool_input.file_path
    if ([string]::IsNullOrWhiteSpace($fp)) { exit 0 }

    $fpNorm = $fp -replace '/', '\'

    if ($fpNorm -notlike "$memDir\*") { exit 0 }
    if ($fpNorm -notlike '*.md')      { exit 0 }
    if (-not (Test-Path -LiteralPath $fpNorm)) { exit 0 }

    if (-not (Test-Path -LiteralPath $vault)) {
        New-Item -ItemType Directory -Force -Path $vault | Out-Null
    }

    $name = Split-Path -Leaf $fpNorm
    Copy-Item -LiteralPath $fpNorm -Destination (Join-Path $vault $name) -Force

    $out = @{ systemMessage = "Memory -> Obsidian gespiegelt: $name"; suppressOutput = $true } | ConvertTo-Json -Compress
    [Console]::Out.Write($out)
    exit 0
}
catch {
    $out = @{ systemMessage = ("Memory->Obsidian Hook-Fehler: " + $_.Exception.Message); suppressOutput = $true } | ConvertTo-Json -Compress
    [Console]::Out.Write($out)
    exit 0
}
