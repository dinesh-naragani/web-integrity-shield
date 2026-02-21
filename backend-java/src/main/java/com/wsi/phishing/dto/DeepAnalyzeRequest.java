package com.wsi.phishing.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * DTO for Level-2 Deep Analysis Request
 * 
 * Sent to: http://localhost:8001/deep-analyze
 */
public class DeepAnalyzeRequest {
    
    @JsonProperty("url")
    private String url;
    
    @JsonProperty("riskScore")
    private Double riskScore;

    public DeepAnalyzeRequest() {
    }

    public DeepAnalyzeRequest(String url, Double riskScore) {
        this.url = url;
        this.riskScore = riskScore;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public Double getRiskScore() {
        return riskScore;
    }

    public void setRiskScore(Double riskScore) {
        this.riskScore = riskScore;
    }

    public boolean isValid() {
        return url != null && !url.trim().isEmpty() && 
               riskScore != null && riskScore >= 0.0 && riskScore <= 1.0;
    }

    @Override
    public String toString() {
        return "DeepAnalyzeRequest{" +
                "url='" + url + '\'' +
                ", riskScore=" + riskScore +
                '}';
    }
}
