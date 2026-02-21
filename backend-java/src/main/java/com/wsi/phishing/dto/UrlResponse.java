package com.wsi.phishing.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * DTO for check-url response
 */
public class UrlResponse {
    
    @JsonProperty("url")
    private String url;
    
    @JsonProperty("riskScore")
    private Double riskScore;
    
    @JsonProperty("level1Label")
    private String level1Label;  // "LEGITIMATE" or "PHISHING"
    
    @JsonProperty("triggerLevel2")
    private Boolean triggerLevel2;  // true if riskScore >= 0.7
    
    @JsonProperty("analysisId")
    private String analysisId;  // UUID from Level-2 (null if not triggered)
    
    @JsonProperty("level2Score")
    private Double level2Score;  // Level-2 risk score (null if not triggered)
    
    @JsonProperty("finalVerdict")
    private String finalVerdict;  // Final verdict after Level-2 (or Level-1 label)
    
    @JsonProperty("reasons")
    private java.util.List<String> reasons;  // Analysis reasons from Level-2

    public UrlResponse() {
    }

    public UrlResponse(String url, Double riskScore, String level1Label, Boolean triggerLevel2) {
        this.url = url;
        this.riskScore = riskScore;
        this.level1Label = level1Label;
        this.triggerLevel2 = triggerLevel2;
        this.reasons = new java.util.ArrayList<>();
    }

    public static Builder builder() {
        return new Builder();
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

    public String getLevel1Label() {
        return level1Label;
    }

    public void setLevel1Label(String level1Label) {
        this.level1Label = level1Label;
    }

    public Boolean getTriggerLevel2() {
        return triggerLevel2;
    }

    public void setTriggerLevel2(Boolean triggerLevel2) {
        this.triggerLevel2 = triggerLevel2;
    }

    public String getAnalysisId() {
        return analysisId;
    }

    public void setAnalysisId(String analysisId) {
        this.analysisId = analysisId;
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

    public java.util.List<String> getReasons() {
        return reasons;
    }

    public void setReasons(java.util.List<String> reasons) {
        this.reasons = reasons;
    }

    public static class Builder {
        private String url;
        private Double riskScore;
        private String level1Label;
        private Boolean triggerLevel2;
        private String analysisId;
        private Double level2Score;
        private String finalVerdict;
        private java.util.List<String> reasons;

        public Builder url(String url) {
            this.url = url;
            return this;
        }

        public Builder riskScore(Double riskScore) {
            this.riskScore = riskScore;
            return this;
        }

        public Builder level1Label(String level1Label) {
            this.level1Label = level1Label;
            return this;
        }

        public Builder triggerLevel2(Boolean triggerLevel2) {
            this.triggerLevel2 = triggerLevel2;
            return this;
        }

        public Builder analysisId(String analysisId) {
            this.analysisId = analysisId;
            return this;
        }

        public Builder level2Score(Double level2Score) {
            this.level2Score = level2Score;
            return this;
        }

        public Builder finalVerdict(String finalVerdict) {
            this.finalVerdict = finalVerdict;
            return this;
        }

        public Builder reasons(java.util.List<String> reasons) {
            this.reasons = reasons;
            return this;
        }

        public UrlResponse build() {
            UrlResponse response = new UrlResponse(url, riskScore, level1Label, triggerLevel2);
            response.setAnalysisId(analysisId);
            response.setLevel2Score(level2Score);
            response.setFinalVerdict(finalVerdict);
            if (reasons != null) {
                response.setReasons(reasons);
            }
            return response;
        }
    }
}
