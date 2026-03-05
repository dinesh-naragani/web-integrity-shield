#!/usr/bin/env pwsh

Write-Host "`n========== TESTING 22-FEATURE MODEL ON BACKEND =========="
Write-Host ""

$base_url = "http://localhost:8080"
$test_urls = @(
    @{ url = "https://chatgpt.com/c/6980f14c"; label = "ChatGPT" },
    @{ url = "https://discord.com/channels/@me/1471875630390972468"; label = "Discord" },
    @{ url = "https://www.youtube.com/watch?v=3EI9YAySwHQ&list=PLqM7alHXFySEgUZPe57"; label = "YouTube" },
    @{ url = "https://github.com/dinesh-naragani/web-integrity-shield"; label = "GitHub" },
    @{ url = "https://google.com"; label = "Google" }
)

$pasCount = 0
$total = 0

foreach ($test in $test_urls) {
    $total++
    $url = $test.url
    $label = $test.label
    
    Write-Host "Test: $label"
    $body = @{ url = $url } | ConvertTo-Json
    $response = Invoke-RestMethod -Method Post -Uri "$base_url/check-url" -ContentType "application/json" -Body $body
    
    $risk = $response.riskScore
    $verdict = if ($risk -lt 0.5) { "SAFE" } else { "RISKY" }
    
    Write-Host "  Risk: $risk  Verdict: $verdict"
    
    if ($risk -lt 0.5) {
        $passCount++
        Write-Host "  Result: PASS"
    } else {
        Write-Host "  Result: FAIL"
    }
    Write-Host ""
}

Write-Host ("Tests passed: $passCount/$total")
Write-Host "========================================================`n"
