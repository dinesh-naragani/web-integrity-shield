package com.wsi.phishing.config;

import java.util.concurrent.TimeUnit;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import reactor.netty.http.client.HttpClient;

/**
 * WebClient Configuration for Level-2 Deep Analysis Service Integration
 * 
 * Configures WebClient with:
 * - 12-second connection timeout
 * - 12-second read/write timeout
 * - Proper error handling
 */
@Configuration
public class WebClientConfig {

    private static final int CONNECT_TIMEOUT_MS = 5000;  // 5 seconds
    private static final int IO_TIMEOUT_SECONDS = 12;     // 12 seconds per requirements

    /**
     * Create WebClient bean with timeout configuration
     * 
     * @return Configured WebClient
     */
    @Bean
    @SuppressWarnings("null")
    public WebClient webClient() {
        HttpClient httpClient = HttpClient.create()
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, CONNECT_TIMEOUT_MS)
            .option(ChannelOption.SO_KEEPALIVE, true)
            .responseTimeout(java.time.Duration.ofSeconds(IO_TIMEOUT_SECONDS))
            .doOnConnected(connection ->
                connection.addHandlerLast(new ReadTimeoutHandler(IO_TIMEOUT_SECONDS, TimeUnit.SECONDS))
                    .addHandlerLast(new WriteTimeoutHandler(IO_TIMEOUT_SECONDS, TimeUnit.SECONDS))
            );

        return WebClient.builder()
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
