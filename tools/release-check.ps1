<#
    release-check.ps1 - Privatsphaere-Pruefung vor jedem Release

    Durchsucht ALLE Dateien, die tatsaechlich im .plugin-Paket landen
    (= von git verwaltete Dateien, ohne die per export-ignore
    ausgeschlossenen), nach persoenlichen Daten und Zugangsschluesseln.

    Aufruf im Repo-Ordner:
        powershell -File tools\release-check.ps1

    Rueckgabe: Exit 0 = sauber, Exit 1 = Fund (Release stoppen!)

    Dieses Script wird NICHT mit ausgeliefert (siehe .gitattributes).
#>

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

# --- Muster, die niemals im Paket stehen duerfen -------------------------
$muster = @(
    @{ Name = 'E-Mail-Adresse';        Regex = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' }
    @{ Name = 'Airtable Token (pat)';  Regex = 'pat[A-Za-z0-9]{14,}' }
    @{ Name = 'Airtable Base-ID';      Regex = '\bapp[A-Za-z0-9]{14}\b' }
    @{ Name = 'Airtable Tabellen-ID';  Regex = '\btbl[A-Za-z0-9]{14}\b' }
    @{ Name = 'Apify API-Token';       Regex = 'apify_api_[A-Za-z0-9]{10,}' }
    @{ Name = 'OpenAI-artiger Key';    Regex = 'sk-[A-Za-z0-9]{20,}' }
    @{ Name = 'Bearer-Token';          Regex = 'Bearer\s+[A-Za-z0-9._-]{20,}' }
    @{ Name = 'Make Szenario-ID';      Regex = '\b(9460562|9480976|9035982|7352445|9428758|9442557|9299095|9382220)\b' }
    @{ Name = 'Persoenlicher Pfad';    Regex = 'C:\\+Users\\+jrang' }
    @{ Name = 'Funnel-Keyword';        Regex = '(?i)\bZwiebel\b' }
    @{ Name = 'Privater Account';      Regex = '(?i)julians[-.]way|@julians\.way' }
    @{ Name = 'Firmenbezug';           Regex = '(?i)secretcreators' }
    @{ Name = 'Anschrift';             Regex = '(?i)t[uü]rkheim|k[oö]nigsberger' }
)

# --- Bewusst erlaubte Ausnahmen (Urheberschaft + Repo-Links) -------------
$erlaubt = @(
    '^\.claude-plugin/(plugin|marketplace)\.json:.*Julian Ranglack'
    '^README\.md:.*jranglack-bot/scb-creator-kit'
    '^\.claude-plugin/marketplace\.json:.*jranglack-bot/scb-creator-kit'
)

# --- Nur Dateien pruefen, die auch ausgeliefert werden -------------------
$dateien = git ls-files | Where-Object { $_ -notlike 'tools/*' }

$funde = @()
foreach ($d in $dateien) {
    if (-not (Test-Path $d)) { continue }
    $inhalt = Get-Content $d -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $inhalt) { continue }
    for ($i = 0; $i -lt $inhalt.Count; $i++) {
        foreach ($m in $muster) {
            if ($inhalt[$i] -match $m.Regex) {
                $eintrag = "$d`:$($i+1): $($inhalt[$i].Trim())"
                $istErlaubt = $false
                foreach ($a in $erlaubt) { if ($eintrag -match $a) { $istErlaubt = $true; break } }
                if (-not $istErlaubt) {
                    $funde += [PSCustomObject]@{
                        Typ    = $m.Name
                        Datei  = $d
                        Zeile  = $i + 1
                        Fund   = $inhalt[$i].Trim()
                    }
                }
            }
        }
    }
}

Write-Output "Geprueft: $($dateien.Count) ausgelieferte Dateien"
Write-Output ""

if ($funde.Count -eq 0) {
    Write-Output "ERGEBNIS: SAUBER - keine persoenlichen Daten im Paket."
    exit 0
} else {
    Write-Output "ERGEBNIS: $($funde.Count) FUND(E) - Release stoppen und pruefen!"
    Write-Output ""
    $funde | Format-Table -AutoSize -Wrap | Out-String | Write-Output
    exit 1
}
