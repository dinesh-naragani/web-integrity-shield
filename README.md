# Web Integrity Shield

Web Integrity Shield is a multi-stage phishing detection system. It combines a Java Level-1 ONNX model with a Python Level-2 deep analysis service and a Chrome extension for real-time alerts.

## Architecture

- Level-1 (Java, Spring Boot): ONNX inference and primary risk scoring.
- Level-2 (Python, FastAPI + Selenium): deep page analysis for suspicious URLs.
- Chrome Extension (Manifest v3): badge + popup UI for user-facing alerts.

Flow:
1. Browser or client sends URL to the Java backend.
2. If riskScore >= 0.7, backend calls Level-2 service.
3. Backend merges results and returns a final verdict.

## Services

### Java Backend (Level-1)
- Endpoint: `POST /check-url`
- Port: `8080`
- Health: `GET /health`

Response includes:
- `riskScore`, `level1Label`, `triggerLevel2`, `level2Status`, `finalVerdict`, and Level-2 fields when available.

### Python Level-2 Service
- Endpoint: `POST /deep-analyze`
- Port: `8001`
- Health: `GET /health`

Uses Selenium headless Chrome to evaluate suspicious factors and returns a weighted score.

### Chrome Extension
- Manifest v3
- Background service worker monitors tab changes
- Popup shows verdict, scores, status, and reasons

## Quick Start (Windows)

### 1) Start Level-2 Service
```powershell
cd C:\Users\N DINESH\Desktop\D\wsi
py -3.11 -m venv .\level2-service\venv311
.\level2-service\venv311\Scripts\python.exe -m pip install -r .\level2-service\requirements.txt
.\level2-service\venv311\Scripts\python.exe .\level2-service\level2_service.py
```

### 2) Start Java Backend
```powershell
cd C:\Users\N DINESH\Desktop\D\wsi
mvn -f backend-java\pom.xml clean package -DskipTests
java -jar .\backend-java\target\wsi-backend-1.0.0.jar
```

### 3) Load Chrome Extension
1. Open `chrome://extensions`
2. Enable Developer mode
3. Click **Load unpacked**
4. Select `C:\Users\N DINESH\Desktop\D\wsi`

## Example Request

```powershell
$body = '{"url":"https://www.google.com"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8080/check-url -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
```

## Response Example

```json
{
  "url": "https://www.google.com",
  "riskScore": 0.025,
  "level1Label": "LEGITIMATE",
  "triggerLevel2": false,
  "level2Status": "NOT_TRIGGERED",
  "analysisId": null,
  "level2Score": null,
  "finalVerdict": "LEGITIMATE",
  "reasons": []
}
```

## Project Structure

```
backend-java/     # Spring Boot backend (Level-1)
level2-service/   # FastAPI + Selenium (Level-2)
ml-python/        # Training and ONNX export
manifest.json     # Chrome extension manifest
background.js     # Extension service worker
popup.html        # Extension UI
popup.js          # UI logic
styles.css        # UI styling
```

## Notes
- Level-2 requires Chrome/Chromium installed locally.
- If Level-2 is offline or times out, backend returns Level-1 result with `level2Status = FALLBACK`.

## Reports
- Phase 2: [PHASE_2_FINAL_REPORT.md](PHASE_2_FINAL_REPORT.md)
- Phase 3: [PHASE_3_SKELETON_REPORT.md](PHASE_3_SKELETON_REPORT.md)
- Phase 4: [PHASE_4_INTEGRATION_REPORT.md](PHASE_4_INTEGRATION_REPORT.md)
- Phase 4.2: [PHASE_4_2_REPORT.md](PHASE_4_2_REPORT.md)
