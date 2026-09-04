package com.appteam.events;

import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ErrorHandler {

    @ExceptionHandler(ServiceException.class)
    public ResponseEntity<ErrorResponse> service(ServiceException error) {
        ErrorResponse body = new ErrorResponse(error.getMessage());

        return ResponseEntity.status(error.getStatus()).body(body);
    }

    @ExceptionHandler(UnsupportedOperationException.class)
    public ResponseEntity<ErrorResponse> unfinished() {
        ErrorResponse body = new ErrorResponse("Implement the event service");

