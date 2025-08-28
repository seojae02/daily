package likelionhackathon13.dailyalley.global.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class SuccessResponse<T> {

    private final HttpStatus status;
    private final String message;
    private final T data;

    public static <T> SuccessResponse<T> of(HttpStatus status, String message, T data) {
        return new SuccessResponse<>(status, message, data);
    }

    public static <T> SuccessResponse<T> of(HttpStatus status, String message) {
        return new SuccessResponse<>(status, message, null);
    }

    public static <T> SuccessResponse<T> ok(String message, T data) {
        return new SuccessResponse<>(HttpStatus.OK, message, data);
    }

    public static <T> SuccessResponse<T> ok(String message) {
        return new SuccessResponse<>(HttpStatus.OK, message, null);
    }

    public static <T> SuccessResponse<T> ok(T data) {
        return new SuccessResponse<>(HttpStatus.OK, "Success", data);
    }
}