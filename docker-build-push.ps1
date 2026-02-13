# Docker build and push to Google Container Registry (GCR)
# Run from project root. Requires: Docker, gcloud CLI, and gcloud auth configured.

param(
    [string]$ProjectId = "soinglobal-telegram",
    [string]$ImageName = "telegram-listener",
    [string]$Tag = "latest"
)

$FullImage = "gcr.io/$ProjectId/${ImageName}:$Tag"

Write-Host "Building image: $FullImage" -ForegroundColor Blue
docker build -t $FullImage .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}

Write-Host "Configuring Docker for GCR (one-time)..." -ForegroundColor Blue
gcloud auth configure-docker gcr.io --quiet

Write-Host "Pushing image: $FullImage" -ForegroundColor Blue
docker push $FullImage

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done. Image pushed: $FullImage" -ForegroundColor Green
} else {
    Write-Host "Push failed. Run: gcloud auth login" -ForegroundColor Red
    exit 1
}
