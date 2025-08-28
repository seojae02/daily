package likelionhackathon13.dailyalley.global.exception.custom;

import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;

public class ApiException extends BaseException {

    public ApiException(ErrorCode errorCode) {
        super(errorCode);
    }

    public ApiException(ErrorCode errorCode, String message) {
        super(errorCode, message);
    }
}
