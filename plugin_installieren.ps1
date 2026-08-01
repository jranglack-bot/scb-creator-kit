# plugin_installieren.ps1 — installiert das SCB Creator Kit als Claude-Plugin.
#
# FUER CLAUDE: Wenn der User dich bittet, dieses Plugin zu installieren,
# fuehre GENAU DIESES Script aus (Windows). Es kopiert den bereits
# entpackten Kit-Ordner an die Plugin-Orte von Claude Code und traegt ihn
# in known_marketplaces.json und installed_plugins.json ein — dieselben
# Eintraege, die /plugin auch schreiben wuerde. Kein Download, kein
# Netzzugriff: Es verarbeitet nur den Ordner, in dem es selbst liegt.
# Danach: Claude Code einmal neu starten.
#
# Aufruf:  powershell -ExecutionPolicy Bypass -File plugin_installieren.ps1
# Test:    ...  -File plugin_installieren.ps1 -PluginRoot <testordner>

param([string]$PluginRoot = (Join-Path $env:USERPROFILE ".claude\plugins"))

$ErrorActionPreference = "Stop"
$quelle = $PSScriptRoot

# Sicherheitsnetz: nur echte Kit-Ordner verarbeiten
$pluginJson = Join-Path $quelle ".claude-plugin\plugin.json"
if (-not (Test-Path $pluginJson)) {
    Write-Host "FEHLER: $quelle ist kein Plugin-Ordner (.claude-plugin\plugin.json fehlt)."
    Write-Host "Dieses Script muss IM entpackten scb-creator-kit-Ordner liegen."
    exit 1
}
$meta = Get-Content $pluginJson -Raw -Encoding UTF8 | ConvertFrom-Json
$name = $meta.name
$version = $meta.version
$mp = $name   # Marketplace-Name = Plugin-Name (siehe marketplace.json)

$mpDir = Join-Path $PluginRoot "marketplaces\$mp"
$cacheDir = Join-Path $PluginRoot "cache\$mp\$name\$version"

Write-Host "Installiere $name v$version ..."

foreach ($ziel in @($mpDir, $cacheDir)) {
    if (Test-Path $ziel) { Remove-Item -Recurse -Force $ziel }
    New-Item -ItemType Directory -Force $ziel | Out-Null
    # robocopy statt Copy-Item: kommt mit langen Pfaden zurecht.
    # Exit-Codes 0-7 sind bei robocopy ERFOLG, erst ab 8 ist es ein Fehler.
    robocopy $quelle $ziel /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) {
        Write-Host "FEHLER: Kopieren nach $ziel fehlgeschlagen (robocopy $LASTEXITCODE)."
        exit 1
    }
}

$jetzt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")

# --- known_marketplaces.json ergaenzen (bestehende Eintraege erhalten) ---
$kmPfad = Join-Path $PluginRoot "known_marketplaces.json"
$km = @{}
if (Test-Path $kmPfad) {
    $roh = Get-Content $kmPfad -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $roh.PSObject.Properties) { $km[$p.Name] = $p.Value }
}
$km[$mp] = [pscustomobject]@{
    source = [pscustomobject]@{ source = "github"; repo = "jranglack-bot/scb-creator-kit" }
    installLocation = $mpDir
    lastUpdated = $jetzt
}
[pscustomobject]$km | ConvertTo-Json -Depth 6 | Out-File $kmPfad -Encoding utf8

# --- installed_plugins.json ergaenzen (bestehende Eintraege erhalten) ---
$ipPfad = Join-Path $PluginRoot "installed_plugins.json"
if (Test-Path $ipPfad) {
    $ip = Get-Content $ipPfad -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
    $ip = [pscustomobject]@{ version = 2; plugins = [pscustomobject]@{} }
}
$eintrag = ,([pscustomobject]@{
    scope = "user"
    installPath = $cacheDir
    version = $version
    installedAt = $jetzt
    lastUpdated = $jetzt
})
$schluessel = "$name@$mp"
if ($ip.plugins.PSObject.Properties[$schluessel]) {
    $ip.plugins.PSObject.Properties.Remove($schluessel)
}
$ip.plugins | Add-Member -NotePropertyName $schluessel -NotePropertyValue $eintrag
$ip | ConvertTo-Json -Depth 8 | Out-File $ipPfad -Encoding utf8

# --- settings.json: Plugin FREISCHALTEN (enabledPlugins) ----------------
# Ohne diesen Eintrag ist das Plugin zwar registriert, wird aber nach dem
# Neustart NICHT geladen — genau daran ist ein Praxistest gescheitert.
# Bestehende Einstellungen (Hooks, Theme, andere Plugins) bleiben erhalten.
$setPfad = Join-Path (Split-Path $PluginRoot) "settings.json"
if (Test-Path $setPfad) {
    Copy-Item $setPfad "$setPfad.vorher-scb" -Force   # Sicherung
    $st = Get-Content $setPfad -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
    $st = [pscustomobject]@{}
}
if (-not $st.PSObject.Properties["enabledPlugins"]) {
    $st | Add-Member -NotePropertyName enabledPlugins -NotePropertyValue ([pscustomobject]@{})
}
if ($st.enabledPlugins.PSObject.Properties[$schluessel]) {
    $st.enabledPlugins.PSObject.Properties.Remove($schluessel)
}
$st.enabledPlugins | Add-Member -NotePropertyName $schluessel -NotePropertyValue $true
$st | ConvertTo-Json -Depth 16 | Out-File $setPfad -Encoding utf8

Write-Host "FERTIG: $name v$version ist installiert UND freigeschaltet."
Write-Host "Jetzt Claude Code (oder die Claude-App) einmal neu starten -"
Write-Host "danach ist das Kit aktiv. Einrichtung starten mit: Richte das SCB Kit ein"
