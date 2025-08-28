package likelionhackathon13.dailyalley.domain.selenium.util;

import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

@Component
public class SeleniumUtil {

    private static final Random RANDOM = new Random();

    public static void shortDelay(double a, double b) {
        long delayMillis;
        if (b > a) {
            delayMillis = (long) (RANDOM.nextDouble(b - a) * 1000 + a * 1000);
        } else {
            // a와 b가 같거나 b가 작을 경우 a만큼 지연
            delayMillis = (long) (a * 1000);
        }

        try {
            Thread.sleep(delayMillis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static boolean hardClick(WebDriver driver, WebElement el) {
        try {
            el.click();
            return true;
        } catch (Exception e) {
            // 클릭 실패 시 Actions, JavaScriptExecutor 순으로 재시도
        }
        try {
            new Actions(driver).moveToElement(el).pause(Duration.ofMillis(50)).click().perform();
            return true;
        } catch (Exception e) {
            // 클릭 실패 시 JavaScriptExecutor로 재시도
        }
        try {
            ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", el);
            shortDelay(0.1, 0.1);
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", el);
            return true;
        } catch (Exception e) {
            // 최종적으로 MouseEvents로 시도
        }
        try {
            ((JavascriptExecutor) driver).executeScript("""
                    const el=arguments[0], o={bubbles:true,cancelable:true,composed:true};
                    el.dispatchEvent(new MouseEvent('mousedown',o));
                    el.dispatchEvent(new MouseEvent('mouseup',o));
                    el.dispatchEvent(new MouseEvent('click',o));
                """, el);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    public static List<Context> listAllContexts(WebDriver driver) {
        List<Context> contexts = new ArrayList<>();
        driver.switchTo().defaultContent();
        contexts.add(new Context("default", null));
        for (int i = 0; i < driver.findElements(By.tagName("iframe")).size(); i++) {
            contexts.add(new Context(String.format("default#iframe[%d]", i), driver.findElements(By.tagName("iframe")).get(i)));
        }

        try {
            driver.switchTo().defaultContent();
            WebElement mainFrame = driver.findElement(By.id("mainFrame"));
            contexts.add(new Context("mainFrame", mainFrame));
            driver.switchTo().frame(mainFrame);
            for (int i = 0; i < driver.findElements(By.tagName("iframe")).size(); i++) {
                contexts.add(new Context(String.format("mainFrame#iframe[%d]", i), driver.findElements(By.tagName("iframe")).get(i)));
            }
        } catch (Exception e) {
            // mainFrame이 없으면 무시
        }
        driver.switchTo().defaultContent();
        return contexts;
    }

    public static boolean clickFinalPublishAnywhere(WebDriver driver) {
        long deadline = System.currentTimeMillis() + Duration.ofSeconds(20).toMillis();
        String[] finalXpaths = {
                "//button[@data-testid='seOnePublishBtn']",
                "//button[contains(@class,'confirm_btn') and .//span[normalize-space()='발행']]",
                "//div[contains(@class,'popup_blog')]//button[.//span[normalize-space()='발행']]",
                "//div[@role='dialog']//button[.//span[normalize-space()='발행']]",
        };

        while (System.currentTimeMillis() < deadline) {
            for (Context ctx : listAllContexts(driver)) {
                try {
                    driver.switchTo().defaultContent();
                    if (ctx.frame != null) {
                        driver.switchTo().frame(ctx.frame);
                    }
                    for (String xp : finalXpaths) {
                        List<WebElement> elems = driver.findElements(By.xpath(xp));
                        if (elems.isEmpty()) {
                            continue;
                        }
                        WebElement btn = elems.get(0);
                        for (int i = 0; i < 6; i++) {
                            boolean isDisabled = (boolean) ((JavascriptExecutor) driver).executeScript(
                                    "return arguments[0].disabled || arguments[0].getAttribute('aria-disabled')==='true';", btn);
                            if (!isDisabled) {
                                break;
                            }
                            shortDelay(0.25, 0.25);
                        }
                        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", btn);
                        shortDelay(0.15, 0.15);
                        if (hardClick(driver, btn)) {
                            System.out.printf("[%s] 최종 발행 클릭 성공: %s%n", ctx.name, xp);
                            return true;
                        }
                    }
                } catch (Exception e) {
                    // 컨텍스트 전환 중 오류 발생 시 무시하고 다음 컨텍스트로
                }
            }
            shortDelay(0.4, 0.4);
        }
        return false;
    }

    public static class Context {
        public String name;
        public WebElement frame;

        public Context(String name, WebElement frame) {
            this.name = name;
            this.frame = frame;
        }
    }
}