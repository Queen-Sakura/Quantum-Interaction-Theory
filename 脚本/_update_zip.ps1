$tmpDir = "C:\Users\sqlan\AppData\Local\Temp\ee2_build"
$modifiedFile = "$tmpDir\ram.ddf"
$entryPath = "EE2X_db/Units/ram.ddf"
$newZip = "$tmpDir\EE2X_new.zip"

# Need to get the latest deployed zip from Z: (was just built with dbunittypeattributes fix)
# But we only need to update ram.ddf entry
$srcZip = "C:\Users\sqlan\AppData\Local\Temp\ee2_build\EE2X_db.zip"

# Actually use the D: backup we just made which is the baseline + attribute fix
# Let's use the latest zip we deployed
$baselineZip = "D:\Games\EE2Test\Empire Earth II\zips_ee2x\EE2X_db.zip"
Copy-Item $baselineZip "$tmpDir\EE2X_db.zip" -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$newBytes = [System.IO.File]::ReadAllBytes($modifiedFile)

$inZip = [System.IO.Compression.ZipFile]::OpenRead("$tmpDir\EE2X_db.zip")
$outZip = [System.IO.Compression.ZipFile]::Open($newZip, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($entry in $inZip.Entries) {
        if ($entry.FullName -eq $entryPath) {
            $newEntry = $outZip.CreateEntry($entryPath)
            $s = $newEntry.Open()
            $s.Write($newBytes, 0, $newBytes.Length)
            $s.Close()
            Write-Host "UPDATED: $entryPath ($($newBytes.Length) bytes)"
        } else {
            $newEntry = $outZip.CreateEntry($entry.FullName)
            $s = $newEntry.Open()
            $inStream = $entry.Open()
            $inStream.CopyTo($s)
            $inStream.Close()
            $s.Close()
        }
    }
} finally {
    $inZip.Dispose()
    $outZip.Dispose()
}

Write-Host "BUILT: $newZip ($((Get-Item $newZip).Length) bytes)"
