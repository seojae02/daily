package likelionhackathon13.dailyalley.Dto;

import lombok.Data;

@Data
public class imgDto {
    private String name;
    private String url;

    public imgDto(String name, String url) {
        this.name = name;
        this.url = url;
    }
}
