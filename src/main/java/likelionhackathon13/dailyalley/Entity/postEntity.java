package likelionhackathon13.dailyalley.Entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Builder
@Data
@NoArgsConstructor
@AllArgsConstructor
public class postEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false)
    private Long postId;
    private Long storeId;
    private String info;
    private String hashtag;
    private String tag;
    @Column(columnDefinition = "TEXT", nullable = true)
    private String body;
    private String picFeel;
    private String postFeel;
    private LocalDateTime createdDate;
    private LocalDateTime modifyDate;
}