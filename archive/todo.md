# 🛡 Web Integrity Shield — Development TODO

Version: v1.0.0  
Goal: Complete submission-ready two-level phishing detection system.

---

## 📊 PROGRESS SUMMARY (UPDATED 2026-02-21)

| Phase | Status | Completion | Component | Notes |
|-------|--------|-----------|-----------|-------|
| **Phase 1** | ✅ COMPLETE | 100% | ML Pipeline | 10.5K URLs, Random Forest, 100% precision |
| **Phase 2** | ✅ COMPLETE | 100% | Java Backend | Spring Boot, ONNX Runtime, REST API |
| **Phase 3** | ⏳ READY | 0% | Deep Analysis | Selenium service (Python FastAPI) |
| **Phase 4** | ⏳ PENDING | 0% | Browser Extension | Manifest V3 (JavaScript) |

**Phase 1 Artifacts** (ml-python/):
- ✅ Feature Extractor: `feature_extractor.py` (7 deterministic features)
- ✅ Trained Model: `models/url_model.pkl` + `models/url_model.onnx` (416 KB)
- ✅ Training Pipeline: `train.py` (Random Forest, 10,500 URLs)
- ✅ Documentation: `PHASE1_COMPLETION_REPORT.md` + `PHASE1_COMPLETION_SUMMARY.txt`

**Phase 2 Artifacts** (backend-java/):
- ✅ Spring Boot Application: `WebIntegrityShieldApplication.java`
- ✅ REST Controller: `UrlController.java` (POST /check-url, GET /health)
- ✅ ONNX Integration: `OnnxModelService.java` (model loads at startup)
- ✅ Feature Extractor: `FeatureExtractor.java` (Java version, matches Python exactly)
- ✅ DTOs: `UrlRequest.java` + `UrlResponse.java`
- ✅ Build: `pom.xml` (Maven, Spring Boot 3.2.0, Java 17, ONNX Runtime 1.17.0)
- ✅ Model: `src/main/resources/models/url_model.onnx` (416 KB in classpath)
- ✅ Documentation: `README.md` + `SETUP_AND_TESTING.md` + `PHASE2_COMPLETION_SUMMARY.txt`

**Cross-Phase Integration**:
- ✅ `INTEGRATION_GUIDE_PHASE1_TO_PHASE2.md` (ML pipeline → Java backend)

---

# 🔵 Phase 0 — Project Setup

## Repository Setup
- [ ] Create root repository: `web-integrity-shield`
- [ ] Create folder structure:
  - [ ] extension/
  - [ ] backend-java/
  - [ ] ml-python/
  - [ ] docs/
- [ ] Initialize Git
- [ ] Create README.md
- [ ] Add .gitignore for Java + Python + Node

---

# ✅ Phase 1 — Level-1 ML (Python → ONNX + PICKLE) — COMPLETE

## 1.1 Dataset Preparation ✅
- [x] Collect phishing URLs (PhishTank/OpenPhish)
- [x] Collect legitimate URLs
- [x] Combine into single dataset
- [x] Label dataset (1 = phishing, 0 = legit)
- [x] Split dataset (70/15/15)
- [x] **Expanded: 123 → 10,500 URLs** (82→10K phishing, 41→500 legitimate)

## 1.2 Feature Engineering ✅
- [x] Implement feature_extractor.py
  - [x] URL length
  - [x] Dot count
  - [x] Hyphen count
  - [x] Special character count
  - [x] HTTPS presence
  - [x] IP address presence
  - [x] Suspicious keyword count
- [x] Ensure deterministic feature order

## 1.3 Model Training ✅
- [x] Train Random Forest (upgraded from Logistic Regression)
- [x] Evaluate: 88.76% accuracy, **100% precision**, 88.2% recall, 93.73% F1
- [x] Save trained model (.pkl)
- [x] 16-core CPU parallelization
- [x] Training time: <1 second for 10.5K URLs

## 1.4 Export to ONNX ✅
- [x] Convert model to ONNX
- [x] Save as: `models/url_model.onnx` (416 KB)
- [x] Validate ONNX inference in Python
- [x] Freeze model for backend integration

---

# ✅ Phase 2 — Java Backend (Spring Boot) — COMPLETE

## 2.1 Project Setup ✅
- [x] Create Spring Boot project
- [x] Configure Maven dependencies:
  - [x] Spring Web Starter
  - [x] ONNX Runtime Java 1.17.0
  - [x] Jackson JSON
  - [x] Lombok
  - [x] Logging (SLF4J + Logback)
- [x] Set Java version to 17
- [x] Create package structure (com.wsi.phishing)

## 2.2 Model Integration ✅
- [x] Load ONNX model at startup (not per-request)
- [x] Implement URL feature extractor in Java
- [x] Match feature order with Python (7 features, exact order)
- [x] Implement ONNX inference method
- [x] Return probability score (0–1)
- [x] Copy url_model.onnx to classpath (resources/models/)

## 2.3 REST API ✅

### Endpoint: POST /check-url ✅
- [x] Validate URL input
- [x] Run Level-1 inference
- [x] Apply threshold logic (>= 0.7)
- [x] Return response JSON:
  - [x] url
  - [x] riskScore
  - [x] level1Label (LEGITIMATE or PHISHING)
  - [x] triggerLevel2 (boolean)

### Additional Endpoints ✅
- [x] GET /health endpoint for health checks

## 2.4 Error Handling ✅
- [x] Handle malformed URLs (400 Bad Request)
- [x] Handle ONNX inference errors (500 Internal Server Error)
- [x] Add timeout protection (30s connection timeout)
- [x] Validate feature extraction
- [x] JSON error response format
- [x] Request/response logging (URL masking)

---

# 🔵 Phase 3 — Deep Analysis (Selenium)

## 3.1 Python Deep Analysis Service
- [ ] Create FastAPI service
- [ ] Create endpoint: POST /deep-check
- [ ] Accept URL JSON input

## 3.2 Selenium Setup
- [ ] Install headless Chrome
- [ ] Configure WebDriver
- [ ] Add 6-second timeout

## 3.3 Feature Extraction (Dynamic)
- [ ] Detect login form presence
- [ ] Count iframes
- [ ] Extract page title
- [ ] Detect external domain references
- [ ] Handle page load exceptions

## 3.4 Risk Scoring
- [ ] Implement rule-based scoring logic
- [ ] Return risk score + verdict

## 3.5 Java Integration
- [ ] Call deep-check API if threshold exceeded
- [ ] Merge Level-1 + Level-2 results
- [ ] Return finalLabel

---

# 🔵 Phase 4 — Browser Extension

## 4.1 Basic Setup
- [ ] Create manifest.json (Manifest V3)
- [ ] Add permissions:
  - [ ] activeTab
  - [ ] scripting
  - [ ] host permissions
- [ ] Create popup.html
- [ ] Create popup.js
- [ ] Create background.js

## 4.2 URL Detection
- [ ] Capture active tab URL
- [ ] Send POST request to backend

## 4.3 UI States

### Loading State
- [ ] Spinner
- [ ] “Analyzing website...” message

### Safe State
- [ ] Green badge
- [ ] Risk score display

### Suspicious State
- [ ] Orange badge
- [ ] Warning text

### Phishing State
- [ ] Red badge
- [ ] Action buttons:
  - [ ] Leave Site
  - [ ] Proceed Anyway

### Error State
- [ ] Display fallback message
- [ ] Add Retry button

---

# 🔵 Phase 5 — In-Page Warning Banner (Optional Enhancement)

- [ ] Inject banner when phishing confirmed
- [ ] Fixed top warning bar
- [ ] Add Leave Site button
- [ ] Ensure high z-index

---

# 🔵 Phase 6 — Performance Testing

- [ ] Measure Level-1 response time (<200ms target)
- [ ] Measure worst-case deep analysis time (≤6s)
- [ ] Test with:
  - [ ] Legitimate URL
  - [ ] Known phishing URL
  - [ ] Malformed URL
- [ ] Confirm no crashes

---

# 🔵 Phase 7 — Documentation

## 7.1 Results
- [ ] Accuracy table
- [ ] Confusion matrix
- [ ] Comparison: Level-1 vs Two-Level

## 7.2 Screenshots
- [ ] Safe detection
- [ ] Suspicious detection
- [ ] Phishing detection
- [ ] Loading state

## 7.3 Final README
- [ ] Architecture diagram
- [ ] Setup instructions
- [ ] API specification
- [ ] Tech stack summary

---

# 🔵 Phase 8 — Pre-Submission Checklist

- [ ] End-to-end demo works 5 times consecutively
- [ ] No hardcoded localhost errors
- [ ] Backend URL configurable
- [ ] ONNX model loads without error
- [ ] Selenium does not hang
- [ ] Code pushed to GitHub
- [ ] Version tagged v1.0.0

---

# ✅ Definition of Done

Project is complete when:
- Level-1 and Level-2 work correctly
- Extension displays final verdict reliably
- Performance targets met
- Documentation ready
- Demo stable
