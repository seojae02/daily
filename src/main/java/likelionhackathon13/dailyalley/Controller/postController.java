package likelionhackathon13.dailyalley.Controller;

import io.swagger.v3.oas.annotations.Operation;
import likelionhackathon13.dailyalley.Dto.postDto;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Service.postService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
public class postController {
    private final postService postService;

    @Operation(
            summary = "가게 게시물 DB 저장 API",
            description = "storeId: 가게 고유 Id, info: 정보, feel: 오늘의 느낌 , tag: 블로그 인지, 인스타 피트나 스토리 인지"
    )
    @PostMapping("/ai")
    public ResponseEntity<?> posttoai(@RequestBody postDto dto) {
        try {
            postService.posttoai(dto);
            return ResponseEntity.ok(Map.of("message", "입력성공"));
        } catch(NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
    @Operation(
            summary = "가게 게시물 AI로 만들어진것 받기 API",
            description = "storeId: 가게 고유 Id /// contents: ai로 만들어진 내용"
    )
    @GetMapping("/ai")
    public ResponseEntity<?> aitopost(@RequestParam Long storeId) {
        try {
            return ResponseEntity.ok(Map.of("contents", postService.aitopost(storeId)));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
}