package likelionhackathon13.dailyalley.Exception;

public class NotExistenceException extends RuntimeException {
    public NotExistenceException() {
        super("존재하지 않는 storeId입니다.");
    }
}
