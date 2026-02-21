package com.wsi.phishing.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * DTO for incoming check-url request
 */
public class UrlRequest {
    
    @JsonProperty("url")
    private String url;

    public UrlRequest() {
    }

    public UrlRequest(String url) {
        this.url = url;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    /**
     * Validate that URL is present and not empty
     */
    public boolean isValid() {
        return url != null && !url.trim().isEmpty();
    }
}
