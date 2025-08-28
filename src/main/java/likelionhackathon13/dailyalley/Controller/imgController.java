package likelionhackathon13.dailyalley.Controller;

import io.minio.MinioClient;
import io.swagger.v3.oas.annotations.Operation;
import likelionhackathon13.dailyalley.Exception.DuplicatenameException;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Exception.NotExistencenameException;
import likelionhackathon13.dailyalley.Service.imgService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
public class imgController {
    private final imgService imgService;
    private MinioClient minioClient;

    @Operation(
            summary = "이미지 업로드 url 신청",
            description = "storeId: 가게 고유 번호, name: 이미지 이름 /// 저장할 이름에 확장자 있어야 합니다.jpg, .png등"
    )
    @GetMapping("/putimg")
    public ResponseEntity<?> uploadimg(@RequestParam long storeId, String name) {
        try{
            return ResponseEntity.ok(Map.of("url", imgService.putimg(storeId, name)));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (DuplicatenameException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage()));
        }
    }
    @Operation(
            summary = "이미지 조회 url 신청",
            description = "storeId: 가게 고유 번호, name: 이미지 이름 /// 조회할 이름에 확장자 있어야 합니다.jpg, .png등"
    )
    @GetMapping("/getimg")
    public ResponseEntity<?> downloadimg(@RequestParam long storeId, String name) {
        try {
            return ResponseEntity.ok(Map.of("url", imgService.getimg(storeId, name)));
        } catch (NotExistencenameException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
    @Operation(
            summary = "이미지 이름 전체 조회",
            description = "storeId: 가게 고유 번호, name: 이미지 이름 /// 조회 할 이름은 temp.jpg 처럼 확장자가 붙어있습니다. storeId를 입력 받아 그 Id의 img 전체를 출력함"
    )
    @GetMapping("/getallimg")
    public ResponseEntity<?> getimgname(@RequestParam long storeId) {
        try {
            return ResponseEntity.ok(imgService.getallimg(storeId));
        } catch (NotExistenceException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
    @Operation(
            summary = "이미지 url로 이름조회",
            description = "body는 url : \"String\" 형태, name: 이미지 이름 /// 조회 할 이름은 1_temp.jpg 처럼 name 앞에 storeId가 붙어있습니다. 이게 파일 이름입니다."
    )
    @PostMapping("/getimg/url")
    public ResponseEntity<?> getimgfurl(@RequestBody Map<String, String> body) {
        try {
            return ResponseEntity.ok(Map.of("name", imgService.getimgfurl(body.get("url"))));
        } catch (NotExistencenameException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", "서버에서 불가피한 문제가 생겼습니다."));
        }
    }
}
