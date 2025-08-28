package likelionhackathon13.dailyalley.Service;

import likelionhackathon13.dailyalley.Dto.snsDto;
import likelionhackathon13.dailyalley.Entity.snsEntity;
import likelionhackathon13.dailyalley.Exception.DuplicateIdException;
import likelionhackathon13.dailyalley.Repository.snsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class snsService {
    private final snsRepository snsRepository;
    private final AES256 aes256;

    public void snswrite(snsDto dto) {
        Optional<snsEntity> temp = snsRepository.findById(dto.getSnsId());
        if (temp.isPresent()) throw new DuplicateIdException();
        try{
            snsEntity entity = snsEntity
                    .builder()
                    .storeId(dto.getStoreId())
                    .snsId(dto.getSnsId())
                    .password(aes256.encrypt(dto.getPassword()))
                    .type(dto.getType())
                    .created_date(LocalDateTime.now())
                    .modify_date(LocalDateTime.now())
                    .build();
            snsRepository.save(entity);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

    }
}