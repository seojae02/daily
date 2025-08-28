package likelionhackathon13.dailyalley.Entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
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
public class imgEntity {
    @Id
    private String name;
    private long storeId;
    @Column(length = 1000)
    private String url;
    private LocalDateTime createDate;
    private LocalDateTime modifyDate;
}
