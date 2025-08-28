package likelionhackathon13.dailyalley.Entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StoreEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false)
    private Long storeId;
    private String name;
    private String type;
    private String location;
    @Column(columnDefinition = "TEXT")
    private String descript;
    private String picFeel;
    private String postFeel;
    private LocalDateTime created_date;
    private LocalDateTime modify_date;
}
