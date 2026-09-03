package com.appteam.events;

public class ServiceException extends RuntimeException {

    private final int status;

    public ServiceException(int status, String message) {
        super(message);

        this.status = status;
    }

    public int getStatus() {
        return status;
    }
}
