Add-Type -AssemblyName System.Security
$cookiePath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Network\Cookies"
Write-Output "Path: $cookiePath"
$exists = Test-Path $cookiePath
Write-Output "Exists: $exists"
if ($exists) {
    $size = (Get-Item $cookiePath).Length
    Write-Output "Size: $size"
}
