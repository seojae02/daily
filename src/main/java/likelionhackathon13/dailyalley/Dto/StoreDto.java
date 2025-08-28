package likelionhackathon13.dailyalley.Dto;

import likelionhackathon13.dailyalley.Entity.StoreEntity;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
public class StoreDto {
    private String name;
    private String type;
    private String location;
    private String descript;

    public void entitytodto(StoreEntity entity) {
        name = entity.getName();
        type = entity.getType();
        location = entity.getLocation();
        descript = entity.getDescript();
    }
}
