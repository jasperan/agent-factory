# Push Industrial PDF URLs to VPS KB Factory
# Run from PowerShell: .\push_urls_to_vps.ps1

$VPS_IP = "72.60.175.144"

$urls = @(
    # Allen-Bradley/Rockwell
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm001_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/rm/1756-rm003_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1769-um021_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um022_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/750-um001_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/520-um001_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/2711p-um001_-en-p.pdf",
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um020_-en-p.pdf",

    # Siemens
    "https://support.industry.siemens.com/cs/attachments/109814829/s71200_system_manual_en-US_en-US.pdf",
    "https://support.industry.siemens.com/cs/attachments/109747136/s71500_system_manual_en-US_en-US.pdf",

    # Mitsubishi
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh080483eng/sh080483engap.pdf",
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh081215eng/sh081215engae.pdf",

    # Omron
    "https://assets.omron.eu/downloads/manual/en/w501_nx-series_cpu_unit_users_manual_en.pdf",
    "https://assets.omron.eu/downloads/manual/en/w504_sysmac_studio_operation_manual_en.pdf",

    # Schneider
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000001578&p_enDocType=User%20guide&p_File_Name=EIO0000001578.00.pdf",
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000000071&p_enDocType=User%20guide&p_File_Name=EIO0000000071.03.pdf"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Push URLs to VPS KB Factory" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS: $VPS_IP"
Write-Host "URLs to push: $($urls.Count)"
Write-Host ""

# Check current status
Write-Host "[1/3] Checking VPS status..." -ForegroundColor Yellow
$queueLen = ssh root@$VPS_IP "docker exec infra_redis_1 redis-cli LLEN kb_ingest_jobs"
$atomCount = ssh root@$VPS_IP "docker exec infra_postgres_1 psql -U rivet -d rivet -t -c 'SELECT COUNT(*) FROM knowledge_atoms;'"
Write-Host "  Queue: $queueLen pending"
Write-Host "  Atoms: $($atomCount.Trim()) in database"
Write-Host ""

# Push URLs
Write-Host "[2/3] Pushing URLs to queue..." -ForegroundColor Yellow
$success = 0
$failed = 0

foreach ($url in $urls) {
    $shortUrl = $url.Substring(0, [Math]::Min(60, $url.Length)) + "..."
    Write-Host "  Pushing: $shortUrl" -NoNewline

    try {
        $result = ssh root@$VPS_IP "docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs '$url'"
        Write-Host " [OK]" -ForegroundColor Green
        $success++
    } catch {
        Write-Host " [FAILED]" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""

# Final status
Write-Host "[3/3] Final status..." -ForegroundColor Yellow
$finalQueue = ssh root@$VPS_IP "docker exec infra_redis_1 redis-cli LLEN kb_ingest_jobs"
Write-Host "  Queue now: $finalQueue pending"
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "  DONE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Pushed: $success URLs"
Write-Host "Failed: $failed URLs"
Write-Host ""
Write-Host "Monitor progress with:" -ForegroundColor Yellow
Write-Host "  ssh root@$VPS_IP 'docker logs infra_rivet-worker_1 --tail 50'"
Write-Host ""
Write-Host "Check atom count:" -ForegroundColor Yellow
Write-Host "  ssh root@$VPS_IP `"docker exec infra_postgres_1 psql -U rivet -d rivet -c 'SELECT COUNT(*) FROM knowledge_atoms;'`""
