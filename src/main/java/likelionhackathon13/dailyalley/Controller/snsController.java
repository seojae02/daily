package likelionhackathon13.dailyalley.Controller;

import io.swagger.v3.oas.annotations.Operation;
import likelionhackathon13.dailyalley.Dto.snsDto;
import likelionhackathon13.dailyalley.Exception.DuplicateIdException;
import likelionhackathon13.dailyalley.Service.snsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequiredArgsConstructor
public class snsController {
    private final snsService snsService;
    @Operation(
            summary = "sns 계정 정보 DB 저장 API",
            description = "storeId: 가게 고유 Id, snsId: sns 계정 아이디, password: sns 계정 비밀번호, type: 네이버 인지 인스타인지"
    )
    @PostMapping("/sns")
    public ResponseEntity<?> snsinfopost(@RequestBody snsDto dto) {
        try {
            snsService.snswrite(dto);
            return ResponseEntity.ok(Map.of("message", "입력 성공"));
        } catch (DuplicateIdException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
}