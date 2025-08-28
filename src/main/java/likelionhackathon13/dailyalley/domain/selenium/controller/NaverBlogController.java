package likelionhackathon13.dailyalley.domain.selenium.controller;

import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import likelionhackathon13.dailyalley.domain.selenium.dto.UploadNaverBlogRequest;
import likelionhackathon13.dailyalley.domain.selenium.service.NaverBlogService;
import likelionhackathon13.dailyalley.global.exception.custom.ApiException;
import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;
import likelionhackathon13.dailyalley.global.response.SuccessResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/naver/blog")
public class NaverBlogController {

    private final NaverBlogService naverBlogService;

    @Operation(
            summary = "네이버 로그인 및 게시물 업로드 자동화 API",
            description = "title: 제목, content: 본문 " +
                    "사진을 첨부할 때는 간단하게 하기 위해서 s3의 경로를 그대로 첨부하여 보이도록 했습니다." +
                    "ex. content: 업로드 테스트 content\\n귀여운 강아지 사진 첨부\\nhttps://image.utoimage.com/preview/cp872722/2022/12/202212008462_500.jpg\\n3번째줄"
    )
    @PostMapping("/upload")
    public ResponseEntity<SuccessResponse<Map<String, String>>> uploadBlogPost(@Valid @RequestBody UploadNaverBlogRequest request) {

            Map<String, String> publishedUrl = naverBlogService.uploadPost(request.getStoreId(), request.getTitle(), request.getContent());
            return ResponseEntity.ok(SuccessResponse.ok(publishedUrl));
    }
}
