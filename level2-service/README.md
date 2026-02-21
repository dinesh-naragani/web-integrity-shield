# Level-2 Deep Analysis Microservice

**Web Integrity Shield – Phase 3**

Port: `8001`

---

## Overview

This FastAPI microservice performs deep Selenium-based phishing analysis on URLs flagged as suspicious by the Level-1 ONNX model (risk score ≥ 0.7).

### Architecture Flow
```
Java Backend (port 8080)
    ↓ HTTP POST /check-url
    ↓
Level-1 ONNX Model
    ↓ Risk Score ≥ 0.7?
    ↓
Level-2 Service (port 8001)
    ↓ POST /deep-analyze
    ↓
Selenium Headless Chrome
    ↓
Return Deep Analysis Verdict
```

---

## Installation

### Prerequisites
- Python 3.9+
- Chrome/Chromium browser (for Selenium)

### Setup

1. **Navigate to service directory:**
   ```bash
   cd level2-service
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start

### Run Service
```bash
python level2_service.py
```

Server will start on `http://localhost:8001`

### Health Check
```bash
curl -X GET http://localhost:8001/health
```

Response:
```json
{
  "status": "OK",
  "service": "Level-2 Deep Analysis",
  "port": 8001,
  "selenium_ready": true
}
```

---

## API Endpoints

### POST `/deep-analyze`

**Deep phishing analysis for a suspicious URL**

**Request:**
```bash
curl -X POST http://localhost:8001/deep-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://paypal-login-verify.com",
    "riskScore": 0.82
  }'
```

**Response (200 OK):**
```json
{
  "url": "https://paypal-login-verify.com",
  "level2Score": 0.91,
  "finalVerdict": "PHISHING",
  "reasons": [
    "Password form detected (1 field)",
    "Suspicious keywords in page title: login, verify",
    "No HTTPS encryption detected"
  ],
  "analysisTime": 3.45,
  "timestamp": "2026-02-21T12:14:42.123456"
}
```

**Input Fields:**
- `url` (string, required): URL to analyze (5-2048 chars)
- `riskScore` (float, required): Level-1 risk score (0.0-1.0)

**Output Fields:**
- `url` (string): Original URL
- `level2Score` (float): Deep analysis risk score (0.0-1.0)
- `finalVerdict` (string): "PHISHING" or "SUSPICIOUS"
  - PHISHING: level2Score ≥ 0.75
  - SUSPICIOUS: level2Score < 0.75
- `reasons` (array): List of suspicious factors detected
- `analysisTime` (float): Seconds taken for analysis
- `timestamp` (string): ISO timestamp

**Error Responses:**
- `400 Bad Request`: Invalid URL or riskScore
- `500 Internal Server Error`: Analysis failure (timeout)

---

### GET `/health`

**Service health check**

```bash
curl -X GET http://localhost:8001/health
```

Response:
```json
{
  "status": "OK",
  "service": "Level-2 Deep Analysis",
  "port": 8001,
  "selenium_ready": true
}
```

---

### GET `/stats`

**Service statistics**

```bash
curl -X GET http://localhost:8001/stats
```

Response:
```json
{
  "service": "Level-2 Deep Analysis",
  "status": "running",
  "selenium_ready": true,
  "config": {
    "timeout": 6,
    "max_batch": 100,
    "port": 8001
  }
}
```

---

## Analysis Factors

The service analyzes 8 factors using Selenium:

### 1. **Login Forms** (Weight: 20%)
- Presence of password input fields
- Login buttons or prompts
- Form elements

### 2. **Hidden Inputs** (Weight: 15%)
- Suspicious hidden form fields
- CSRF/CSRF tokens (tracking)
- Data collection fields

### 3. **External Scripts** (Weight: 15%)
- Scripts from suspicious domains
- Analytics/tracking scripts
- Redirect services

### 4. **URL Changes** (Weight: 8%)
- Redirect detection
- Domain switching

### 5. **Page Title Keywords** (Weight: 8%)
- Suspicious keywords: login, verify, urgent, billing, etc.
- Impersonation indicators

### 6. **Suspicious Iframes** (Weight: 8%)
- Hidden iframes
- Cross-domain iframes

### 7. **Security Issues** (Weight: 8%)
- Missing HTTPS
- Mixed content warnings

### 8. **Form Behavior** (Weight: 8%)
- External form submission
- Unusual form patterns

---

## Scoring Algorithm

### Level-2 Score Calculation
```
Level2Score = (Level1Score × 0.40) + (sum of weighted factor scores)

Example:
  Level1Score = 0.82
  LoginForm score = 0.3 × 0.20 = 0.06
  ExternalScripts score = 0.15 × 0.15 = 0.0225
  TitleKeywords score = 0.2 × 0.08 = 0.016
  ...
  
  Total: 0.328 + 0.82×0.40 = 0.656 + 0.04 = 0.696... (simplified)
```

### Verdict Determination
```
If level2Score >= 0.75: PHISHING
Else: SUSPICIOUS
```

---

## Configuration

Edit `config.py` to customize:

```python
SERVICE_PORT = 8001          # Service port
SELENIUM_TIMEOUT = 6         # Page load timeout (seconds)
REQUEST_TIMEOUT = 10         # Total request timeout (seconds)
HEADLESS_MODE = True         # Run Chrome headless
MAX_BATCH_SIZE = 100         # Max batch analysis size
```

---

## Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `level2_service.log` (DEBUG and above)

Log rotation: 10MB per file, keeps 3 backups

---

## Integration with Java Backend

### Java Backend Calls Level-2 Service

When Level-1 model returns risk ≥ 0.7:

**Java Code (UrlController.java):**
```java
if (riskScore >= 0.7) {
    // Call Level-2 service
    DeepAnalysisResponse level2 = httpClient.post(
        "http://localhost:8001/deep-analyze",
        new DeepAnalyzeRequest(url, riskScore)
    );
    
    return new UrlResponse(url, riskScore, "PHISHING", true);
}
```

---

## Timeout Protection

All requests have timeout protection:

```python
# 6 seconds: Selenium page load timeout
SELENIUM_TIMEOUT = 6

# 10 seconds: Total request timeout
REQUEST_TIMEOUT = 10
```

If analysis exceeds 10 seconds, request is terminated with 500 error.

---

## Troubleshooting

### Chrome/Chromium Not Found
```bash
# Install Chrome (Ubuntu)
sudo apt-get install chromium-browser

# Or use webdriver-manager (automatic)
# Already included in requirements.txt
```

### Selenium Timeout
- Check URL accessibility
- Increase `SELENIUM_TIMEOUT` in config.py
- Check network/firewall rules

### Service Won't Start
```bash
# Check port availability
lsof -i :8001  # On Linux/Mac
netstat -ano | findstr :8001  # On Windows

# Kill process if needed
kill -9 <PID>  # On Linux/Mac
```

### SSL Certificate Errors
Selenium is configured to ignore SSL warnings by default.

---

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

### Example Using Python Requests
```python
import requests

url = "https://paypal-login-verify.com"
response = requests.post(
    "http://localhost:8001/deep-analyze",
    json={
        "url": url,
        "riskScore": 0.82
    }
)
print(response.json())
```

---

## Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Startup time | 3-5 seconds |
| Chrome initialization | 2-3 seconds |
| Average page analysis | 3-5 seconds |
| Total request time | 4-8 seconds (within 10s limit) |
| Memory usage | 200-400 MB |

---

## Security Notes

- ✅ Headless Chrome runs isolated
- ✅ No JavaScript execution (by default)
- ✅ No image loading (performance)
- ✅ Timeout protection against stalled pages
- ✅ Structured error handling (no info leaks)

---

## What's NOT Included (Future Work)

- Database storage for analysis history
- Batch analysis job queue
- Machine learning for unknown patterns
- Screenshot capture
- JavaScript execution analysis
- Content security policy analysis

---

## Testing

### Unit Tests (Future)
```bash
pytest test_selenium_analyzer.py -v
```

### Manual Testing
```bash
# Test with legitimate URL
curl -X POST http://localhost:8001/deep-analyze \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.google.com","riskScore":0.1}'

# Test with suspicious URL
curl -X POST http://localhost:8001/deep-analyze \
  -H "Content-Type: application/json" \
  -d '{"url":"https://paypal-login-verify.com","riskScore":0.82}'
```

---

## License

Part of Web Integrity Shield – Educational Project

---

## Support

For issues or questions, refer to:
- [PHASE_2_FINAL_REPORT.md](../PHASE_2_FINAL_REPORT.md) - Phase 2 backend
- [INTEGRATION_GUIDE_PHASE1_TO_PHASE2.md](../INTEGRATION_GUIDE_PHASE1_TO_PHASE2.md) - Integration details

---

*Version: 1.0.0*  
*Last Updated: February 21, 2026*
