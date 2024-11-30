# Define the GitHub repository and API endpoint
$repo = "ivanmeler/SamFirm_Reborn"
$apiUrl = "https://api.github.com/repos/$repo/releases/latest"

# Fetch the latest release information
$response = Invoke-RestMethod -Uri $apiUrl

# Filter for the release ZIP (exclude source code)
$releaseZip = $response.assets | Where-Object { 
    ($_ -match "\.zip$") -and 
    ($_.name -notmatch "source") 
} | Select-Object -First 1 -ExpandProperty browser_download_url

# Download the release ZIP
if ($releaseZip) {
    $fileName = Split-Path $releaseZip -Leaf
    Invoke-WebRequest -Uri $releaseZip -OutFile $fileName
    Write-Output "Downloaded $fileName"
} else {
    Write-Output "No release ZIP file found for the latest release."
}
