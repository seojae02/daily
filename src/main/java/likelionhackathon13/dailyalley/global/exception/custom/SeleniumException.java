package likelionhackathon13.dailyalley.global.exception.custom;

import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;

public class SeleniumException  extends BaseException {

  public SeleniumException(ErrorCode errorCode) {
    super(errorCode);
  }

  public SeleniumException(ErrorCode errorCode, String message) {
    super(errorCode, message);
  }
}
