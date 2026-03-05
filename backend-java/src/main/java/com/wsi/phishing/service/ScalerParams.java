package com.wsi.phishing.service;

import java.util.List;

public class ScalerParams {
    private int feature_count;
    private List<Double> mean;
    private List<Double> scale;

    public int getFeature_count() {
        return feature_count;
    }

    public void setFeature_count(int feature_count) {
        this.feature_count = feature_count;
    }

    public List<Double> getMean() {
        return mean;
    }

    public void setMean(List<Double> mean) {
        this.mean = mean;
    }

    public List<Double> getScale() {
        return scale;
    }

    public void setScale(List<Double> scale) {
        this.scale = scale;
    }
}
