package likelionhackathon13.dailyalley.global.exception.error;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    /** ========== 400 BAD_REQUEST (잘못된 요청) ========== **/
    BAD_REQUEST(HttpStatus.BAD_REQUEST, "B001", "잘못된 요청입니다."),
    INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "B002", "입력 값이 올바르지 않습니다."),
    MISSING_REQUIRED_PARAMETER(HttpStatus.BAD_REQUEST, "B003", "필수 요청 파라미터가 누락되었습니다."),
    INVALID_JSON_FORMAT(HttpStatus.BAD_REQUEST, "B004", "잘못된 JSON 형식입니다."),
    UNSUPPORTED_OPERATION(HttpStatus.BAD_REQUEST, "B005", "지원하지 않는 작업입니다."),

    /** ========== 401 UNAUTHORIZED (인증 오류) ========== **/
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "A001", "인증이 필요합니다."),
    INVALID_CREDENTIALS(HttpStatus.UNAUTHORIZED, "A002", "아이디 또는 비밀번호가 일치하지 않습니다."),
    ACCESS_TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "A003", "Access Token이 만료되었습니다."),
    INVALID_ACCESS_TOKEN(HttpStatus.UNAUTHORIZED, "A004", "유효하지 않은 Access Token입니다."),
    REFRESH_TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "A005", "Refresh Token이 만료되었습니다."),
    INVALID_REFRESH_TOKEN(HttpStatus.UNAUTHORIZED, "A006", "유효하지 않은 Refresh Token입니다."),
    JWT_SIGNATURE_INVALID(HttpStatus.UNAUTHORIZED, "A007", "JWT 서명이 유효하지 않습니다."),
    JWT_MALFORMED(HttpStatus.UNAUTHORIZED, "A008", "JWT 형식이 올바르지 않습니다."),
    INVALID_TOKEN_CATEGORY(HttpStatus.UNAUTHORIZED, "A09", "Token 카테고리가 유효하지 않습니다."),
    TOKEN_NOT_PROVIDED(HttpStatus.UNAUTHORIZED, "A010", "Token이 제공되지 않았습니다."),
    EMAIL_ALREADY_REGISTERED_WITH_OTHER_PROVIDER(HttpStatus.UNAUTHORIZED, "A011", "이미 계정이 존재하는 이메일에 대해 추가적인 계정 생성을 제한합니다."),
    ENCRYPTION_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "A012", "데이터 암호화 과정에서 오류가 발생했습니다."),
    DECRYPTION_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "A013", "데이터 복호화 과정에서 오류가 발생했습니다."),

    /** ========== 403 FORBIDDEN (권한 부족) ========== **/
    FORBIDDEN(HttpStatus.FORBIDDEN, "F001", "접근이 거부되었습니다."),

    /** ========== 404 NOT_FOUND (리소스 없음) ========== **/
    RESOURCE_NOT_FOUND(HttpStatus.NOT_FOUND, "N001", "요청한 리소스를 찾을 수 없습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "N002", "사용자를 찾을 수 없습니다."),

    /** ========== 409 CONFLICT (비즈니스 충돌) ========== **/
    DUPLICATE_RESOURCE(HttpStatus.CONFLICT, "C001", "이미 존재하는 리소스입니다."),
    CONFLICT_OPERATION(HttpStatus.CONFLICT, "C002", "요청이 현재 상태와 충돌합니다."),

    /** ========== 500 INTERNAL_SERVER_ERROR (서버 오류) ========== **/
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "S001", "서버 내부 오류가 발생했습니다."),
    DATABASE_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "S002", "데이터베이스 처리 중 오류가 발생했습니다."),
    EXTERNAL_SERVICE_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "S003", "외부 서비스 호출 중 오류가 발생했습니다."),
    UNKNOWN_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "S004", "알 수 없는 오류가 발생했습니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;
}