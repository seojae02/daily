package likelionhackathon13.dailyalley.Service;

import likelionhackathon13.dailyalley.Dto.StoreDto;
import likelionhackathon13.dailyalley.Dto.contentsDto;
import likelionhackathon13.dailyalley.Entity.StoreEntity;
import likelionhackathon13.dailyalley.Entity.postEntity;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Exception.NotExistencenameException;
import likelionhackathon13.dailyalley.Repository.StoreRepository;
import likelionhackathon13.dailyalley.Repository.postRepository;
import lombok.RequiredArgsConstructor;
import org.apache.catalina.Store;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class StoreService {
    private final StoreRepository storeRepository;
    private final postRepository postRepository;

    public long write(StoreDto dto){
        try {
            StoreEntity entity = StoreEntity
                    .builder()
                    .name(dto.getName())
                    .type(dto.getType())
                    .location(dto.getLocation())
                    .descript(dto.getDescript())
                    .created_date(LocalDateTime.now())
                    .modify_date(LocalDateTime.now())
                    .build();
            storeRepository.save(entity);
            return entity.getStoreId();
        } catch(Exception e) {
            throw new RuntimeException();
        }
    }

    public StoreDto findById(Long id) {
        Optional<StoreEntity> temp = storeRepository.findById(id);
        if (temp.isEmpty()) throw new NotExistenceException();
        StoreDto dto = new StoreDto();
        dto.entitytodto(temp.get());
        return dto;
    }

    public void contents(contentsDto dto){
        Optional<StoreEntity> temp = storeRepository.findById(dto.getStoreId());
        if(temp.isEmpty()) throw new NotExistenceException();
        temp.get().setPicFeel(dto.getPicFeel());
        temp.get().setPostFeel(dto.getPostFeel());
        temp.get().setModify_date(LocalDateTime.now());
        storeRepository.save(temp.get());
    }

    public contentsDto getcontents(long storeId) {
        Optional<StoreEntity> temp = storeRepository.findById(storeId);
        if(temp.isEmpty()) throw new NotExistenceException();
        contentsDto dto = new contentsDto();
        dto.setStoreId(storeId);
        dto.setPicFeel(temp.get().getPicFeel());
        dto.setPostFeel(temp.get().getPostFeel());
        return dto;
    }
}
