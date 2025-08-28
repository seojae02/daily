package likelionhackathon13.dailyalley.Controller;

import io.swagger.v3.oas.annotations.Operation;
import likelionhackathon13.dailyalley.Dto.StoreDto;
import likelionhackathon13.dailyalley.Dto.contentsDto;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Service.StoreService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
public class StoreController {
    private final StoreService storeService;

    @Operation(
            summary = "가게 정보 DB 저장 API",
            description = "name: 가게 이름, type: 가게 업종, location: 가게 위치, descript: 가게 설명 /// storeId: 가게 고유 Id"
    )
    @PostMapping("/store")
    public ResponseEntity<?> storeinfopost(@RequestBody StoreDto dto) {
        try {
            return ResponseEntity.ok(Map.of("message", "입력 성공", "storeId", storeService.write(dto)));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }

    @Operation(
            summary = "가게 정보 DB 조회 API",
            description = "name: 가게 이름, type: 가게 업종, location: 가게 위치, descript: 가게 설명 /// storeId: 가게 고유 Id"
    )
    @GetMapping("/store")
    public ResponseEntity<?> storeinfoget(@RequestParam Long storeId) {
        try {
            return ResponseEntity.ok(Map.of("url", storeService.findById(storeId)));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
    @Operation(
            summary = "contents 느낌 저장 API",
            description = "storeId: 가게 고유번호, picFeel: 사진 느낌, postFeel: 게시물 느낌 ///"
    )
    @PostMapping("/contents")
    public ResponseEntity<?> contents(@RequestBody contentsDto dto) {
        try {
            storeService.contents(dto);
            return ResponseEntity.ok(Map.of("message", "입력성공"));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }

    @GetMapping("/contents")
    public ResponseEntity<?> contents(@RequestParam long storeId) {
        try{
            return ResponseEntity.ok(storeService.getcontents(storeId));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
}
