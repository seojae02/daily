package likelionhackathon13.dailyalley.domain.selenium.service;

import io.github.bonigarcia.wdm.WebDriverManager;
import likelionhackathon13.dailyalley.Entity.snsEntity;
import likelionhackathon13.dailyalley.Repository.snsRepository;
import likelionhackathon13.dailyalley.Service.AES256;
import likelionhackathon13.dailyalley.domain.selenium.util.SeleniumUtil;
import likelionhackathon13.dailyalley.global.exception.custom.SeleniumException;
import likelionhackathon13.dailyalley.global.exception.error.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class NaverBlogService {

    private final SeleniumUtil seleniumUtil;
    private final snsRepository snsRepository;
    private final AES256 aes256;

    private WebDriver driver;

    public Map<String, String> uploadPost(Long storeId, String title, String content) {

        snsEntity snsEntity = snsRepository.findByStoreId(storeId)
                .orElseThrow(() -> new SeleniumException(ErrorCode.RESOURCE_NOT_FOUND, "snsEntity not found"));
        String naverId = snsEntity.getSnsId();

        String naverPw = "";
        try {
            naverPw = aes256.decrypt(snsEntity.getPassword());
        } catch (Exception e) {
            throw new SeleniumException(ErrorCode.DECRYPTION_ERROR);
        }

        // WebDriverManager를 사용해 OS에 맞는 ChromeDriver 자동 설정
        WebDriverManager.chromedriver().setup();

        ChromeOptions options = new ChromeOptions();

        options.addArguments("--headless=new");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--disable-gpu");

        driver = new ChromeDriver(options);
        WebDriverWait wait;

        try {
            System.out.println("naver login page connect...");
            driver.get("https://nid.naver.com/nidlogin.login");
            wait = new WebDriverWait(driver, Duration.ofSeconds(20));

            // 아이디 입력
            WebElement idField = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("id")));
            ((JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];", idField, naverId);
            System.out.println("successful id input");

            // 비밀번호 입력
            WebElement pwField = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("pw")));
            ((JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];", pwField, naverPw);
            System.out.println("successful pw input");

            // 로그인 버튼 클릭
            wait.until(ExpectedConditions.elementToBeClickable(By.id("log.login"))).click();
            System.out.println("login button click");


            // 로그인 성공 대기
            wait.until(driver -> !driver.getCurrentUrl().contains("nidlogin"));
            System.out.println("login OK");

            // ===== 글쓰기 진입 =====
            String blogId = naverId;
            String writeUrl = String.format("https://blog.naver.com/%s?Redirect=Write", blogId);
            System.out.println("\nblog input page connect: " + writeUrl);
            driver.get(writeUrl);
            seleniumUtil.shortDelay(0.2, 1.0);

            System.out.println("editor fraim connecting...");
            driver.switchTo().defaultContent();
            try {
                wait.until(ExpectedConditions.frameToBeAvailableAndSwitchToIt(By.id("mainFrame")));
            } catch (TimeoutException e) {
                throw new IllegalStateException("editor fraim failed");
            }
            seleniumUtil.shortDelay(0.2, 0.4);

            // 팝업이 나타날 수 있으므로 잠시 대기
            seleniumUtil.shortDelay(1.0, 1.5);

            // "작성 중인 글이 있습니다." 팝업이 나타나는지 확인
            try {
                // 팝업 컨테이너 요소가 나타날 때까지 최대 5초 대기
                WebElement popup = wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath("//div[contains(@class, 'se-popup-container') and .//strong[normalize-space()='작성 중인 글이 있습니다.']]")));

                System.out.println("click the 'Cancel' button...");

                // 팝업 내의 '취소' 버튼을 찾아 클릭
                WebElement cancelButton = popup.findElement(By.xpath(".//button[contains(@class, 'se-popup-button-cancel') and .//span[normalize-space()='취소']]"));
                seleniumUtil.hardClick(driver, cancelButton);

                // 팝업이 사라질 때까지 대기하여 다음 동작에 방해가 없도록 함
                wait.until(ExpectedConditions.invisibilityOf(popup));
                System.out.println("success clicking the 'Cancel' button");

            } catch (TimeoutException e) {
                // 팝업이 나타나지 않은 경우, 예외를 무시하고 정상 흐름을 진행
                System.out.println("The pop-up for the post.");
            }

            // 제목 입력
            System.out.println("input title...");
            WebElement titlePlaceholder = wait.until(
                    ExpectedConditions.elementToBeClickable(By.xpath("//div[contains(@class,'se-title-text')]//span[contains(@class,'se-placeholder') and contains(@class,'se-fs32')]"))
            );
            titlePlaceholder.click();
            seleniumUtil.shortDelay(0.2, 0.3);

            // 사람처럼 타이핑
            Actions actions = new Actions(driver);
            for (char ch : title.toCharArray()) {
                actions.sendKeys(String.valueOf(ch)).pause(Duration.ofMillis(new Random().nextInt(71) + 30)).perform();
            }
            seleniumUtil.shortDelay(0.2, 0.3);

            // 본문으로 이동
            actions.sendKeys(Keys.ENTER).pause(Duration.ofMillis(new Random().nextInt(201) + 150)).perform();
            seleniumUtil.shortDelay(0.3, 0.6);

            // 본문으로 이동했는지 확인 및 재시도
            try {
                boolean moved = (boolean) ((JavascriptExecutor) driver).executeScript("""
                        const a = document.activeElement;
                        if (!a) return false;
                        const inBody = a.closest && a.closest("div[data-a11y-title='본문'], .se-component.se-text");
                        const isParagraph = a.matches && a.matches("p.se-text-paragraph, [contenteditable='true'], [role='textbox']");
                        return !!(inBody || isParagraph);
                    """);
                if (!moved) {
                    actions.sendKeys(Keys.ENTER).pause(Duration.ofMillis(new Random().nextInt(151) + 100)).perform();
                    seleniumUtil.shortDelay(0.2, 0.4);
                }
            } catch (Exception ignored) {
            }

            // 본문 입력
            System.out.println("input contents...");
            List<String> bodyLines = Arrays.stream(content.split("\\r?\\n"))
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());

            while (!bodyLines.isEmpty() && bodyLines.get(0).isEmpty()) { bodyLines.remove(0); }
            while (!bodyLines.isEmpty() && bodyLines.get(bodyLines.size() - 1).isEmpty()) { bodyLines.remove(bodyLines.size() - 1); }

            Actions actions2 = new Actions(driver);
            for (int i = 0; i < bodyLines.size(); i++) {
                String line = bodyLines.get(i);
                if (!line.isEmpty()) {
                    for (char ch : line.toCharArray()) {
                        actions2.sendKeys(String.valueOf(ch)).pause(Duration.ofMillis(new Random().nextInt(61) + 20));
                    }
                }
                if (i < bodyLines.size() - 1) {
                    actions2.sendKeys(Keys.ENTER).pause(Duration.ofMillis(new Random().nextInt(161) + 120));
                }
            }
            actions2.perform();
            seleniumUtil.shortDelay(0.2, 1.0);

            // "도움말" 팝업이 나타나는지 확인하고 닫기
            try {
                // 도움말 패널이 나타날 때까지 최대 5초 대기
                WebElement helpPanel = wait.until(ExpectedConditions.presenceOfElementLocated(By.xpath("//article[contains(@class, 'se-help-panel')]")));

                System.out.println("Help panel detection");

                // 패널 내의 닫기 버튼을 찾아 클릭
                WebElement closeButton = helpPanel.findElement(By.xpath(".//button[contains(@class, 'se-help-panel-close-button')]"));
                seleniumUtil.hardClick(driver, closeButton);

                // 패널이 사라질 때까지 대기
                wait.until(ExpectedConditions.invisibilityOf(helpPanel));
                System.out.println("Click the 'Close' button to complete.");

            } catch (TimeoutException e) {
                // 도움말 패널이 나타나지 않은 경우, 예외를 무시하고 정상 흐름을 진행
                System.out.println("The help panel did not appear.");
            }


            // 1차 발행
            System.out.println("[mainFrame] Click on the first issue...");
            WebElement firstPublishBtn = wait.until(ExpectedConditions.elementToBeClickable(By.xpath("//span[normalize-space()='발행']/ancestor::button")));
            seleniumUtil.hardClick(driver, firstPublishBtn);
            seleniumUtil.shortDelay(0.4, 0.7);

            // 최종 발행
            System.out.println("Navigate/click the final publish button...");
            if (!seleniumUtil.clickFinalPublishAnywhere(driver)) {
                throw new TimeoutException("I can't find the final publish button anywhere.");
            }

            try {
                new WebDriverWait(driver, Duration.ofSeconds(10)).until(ExpectedConditions.invisibilityOfElementLocated(By.xpath("//button[@data-testid='seOnePublishBtn']")));
            } catch (TimeoutException ignored) {
            }

            String originalUrl = driver.getCurrentUrl();
            new WebDriverWait(driver, Duration.ofSeconds(20)).until(ExpectedConditions.not(ExpectedConditions.urlToBe(originalUrl)));

            String returnUrl = driver.getCurrentUrl();
            System.out.println("\nYour blog post request has been completed!");
            System.out.println("Published blog URL: " + returnUrl);

            return Map.of("upload-url", returnUrl);

        } catch (Exception e) {
            System.err.println("Error occurred while logging in/uploading: " + e.getMessage());
            throw new RuntimeException(e);
        } finally {
            if (driver != null) {
                System.out.println("End in 10 seconds");
                SeleniumUtil.shortDelay(0.1, 0.5);
                driver.quit();
            }
        }
    }
}