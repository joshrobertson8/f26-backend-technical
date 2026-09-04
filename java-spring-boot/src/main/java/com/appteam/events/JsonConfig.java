package com.appteam.events;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.CoercionAction;
import com.fasterxml.jackson.databind.cfg.CoercionInputShape;
import com.fasterxml.jackson.databind.cfg.MutableCoercionConfig;
import com.fasterxml.jackson.databind.type.LogicalType;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class JsonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();

        mapper.enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
        mapper.enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

        MutableCoercionConfig strings = mapper.coercionConfigFor(LogicalType.Textual);

        strings.setCoercion(CoercionInputShape.Integer, CoercionAction.Fail);
        strings.setCoercion(CoercionInputShape.Float, CoercionAction.Fail);
        strings.setCoercion(CoercionInputShape.Boolean, CoercionAction.Fail);

        return mapper;
    }
}
