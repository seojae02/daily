package likelionhackathon13.dailyalley.Entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
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
public class snsEntity {
    private Long storeId;
    @Id
    private String snsId;
    private String password;
    private String type;
    private LocalDateTime created_date;
    private LocalDateTime modify_date;
}