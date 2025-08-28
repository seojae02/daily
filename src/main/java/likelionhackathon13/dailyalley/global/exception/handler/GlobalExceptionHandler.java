package likelionhackathon13.dailyalley.global.exception.handler;

import jakarta.servlet.http.HttpServletRequest;
import likelionhackathon13.dailyalley.global.exception.custom.ApiException;
import likelionhackathon13.dailyalley.global.exception.custom.AuthException;
import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;
import likelionhackathon13.dailyalley.global.response.ErrorResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;


@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGlobalException(Exception ex, HttpServletRequest request) {

        log.error("Unhandled Exception: {}", ex.getMessage(), ex);

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ErrorResponse.of(ErrorCode.INTERNAL_SERVER_ERROR, request.getRequestURI()));
    }

    @ExceptionHandler(AuthException.class)
    public ResponseEntity<ErrorResponse> handleAuthException(AuthException ex, HttpServletRequest request) {

        log.error("Auth exception: {}, messsage: {}", ex.getClass().getSimpleName(), ex.getMessage());

        ErrorResponse errorResponse = ErrorResponse.of(ex.getErrorCode(), request.getRequestURI());
        return ResponseEntity.status(ex.getErrorCode().getStatus()).body(errorResponse);
    }

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handleApiException(ApiException ex, HttpServletRequest request) {

        log.error("Api exception: {}, messsage: {}", ex.getClass().getSimpleName(), ex.getMessage());

        ErrorResponse errorResponse = ErrorResponse.of(ex.getErrorCode(), request.getRequestURI());
        return ResponseEntity.status(ex.getErrorCode().getStatus()).body(errorResponse);
    }
}
