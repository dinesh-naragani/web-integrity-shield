package com.wsi.phishing.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * DTO for Level-2 Deep Analysis Response
 * 
 * Received from: http://localhost:8001/deep-analyze
 */
public class DeepAnalyzeResponse {
    
    @JsonProperty("analysisId")
    private String analysisId;
    
    @JsonProperty("url")
    private String url;
    
    @JsonProperty("level2Score")
    private Double level2Score;
    
    @JsonProperty("finalVerdict")
    private String finalVerdict;  // "PHISHING" or "SUSPICIOUS"
    
    @JsonProperty("reasons")
    private List<String> reasons;
    
    @JsonProperty("analysisTime")
    private Double analysisTime;
    
    @JsonProperty("timestamp")
    private String timestamp;

    public DeepAnalyzeResponse() {
    }

    public DeepAnalyzeResponse(String analysisId, String url, Double level2Score, 
                               String finalVerdict, List<String> reasons, 
                               Double analysisTime, String timestamp) {
        this.analysisId = analysisId;
        this.url = url;
        this.level2Score = level2Score;
        this.finalVerdict = finalVerdict;
        this.reasons = reasons;
        this.analysisTime = analysisTime;
        this.timestamp = timestamp;
    }

    public String getAnalysisId() {
        return analysisId;
    }

    public void setAnalysisId(String analysisId) {
        this.analysisId = analysisId;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public Double getLevel2Score() {
        return level2Score;
    }

    public void setLevel2Score(Double level2Score) {
        this.level2Score = level2Score;
    }

    public String getFinalVerdict() {
        return finalVerdict;
    }

    public void setFinalVerdict(String finalVerdict) {
        this.finalVerdict = finalVerdict;
    }

    public List<String> getReasons() {
        return reasons;
    }

    public void setReasons(List<String> reasons) {
        this.reasons = reasons;
    }

    public Double getAnalysisTime() {
        return analysisTime;
    }

    public void setAnalysisTime(Double analysisTime) {
        this.analysisTime = analysisTime;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public boolean isValid() {
        return analysisId != null && !analysisId.trim().isEmpty() &&
               url != null && !url.trim().isEmpty() &&
               level2Score != null && level2Score >= 0.0 && level2Score <= 1.0 &&
               finalVerdict != null && !finalVerdict.trim().isEmpty();
    }

    @Override
    public String toString() {
        return "DeepAnalyzeResponse{" +
                "analysisId='" + analysisId + '\'' +
                ", url='" + url + '\'' +
                ", level2Score=" + level2Score +
                ", finalVerdict='" + finalVerdict + '\'' +
                ", reasonsCount=" + (reasons != null ? reasons.size() : 0) +
                ", analysisTime=" + analysisTime +
                '}';
    }
}
