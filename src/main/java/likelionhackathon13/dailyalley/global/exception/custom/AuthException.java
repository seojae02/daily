package likelionhackathon13.dailyalley.global.exception.custom;

import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;

public class AuthException extends BaseException {

    public AuthException(ErrorCode errorCode) {
        super(errorCode);
    }

    public AuthException(ErrorCode errorCode, String message) {
        super(errorCode, message);
    }
}
