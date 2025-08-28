package likelionhackathon13.dailyalley.Exception;

public class DuplicateIdException extends RuntimeException {
    public DuplicateIdException() {
        super("이미 등록되어 있는 ID 입니다.");
    }
}
