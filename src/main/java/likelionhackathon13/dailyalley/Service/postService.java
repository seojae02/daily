package likelionhackathon13.dailyalley.Service;

import likelionhackathon13.dailyalley.Dto.postDto;
import likelionhackathon13.dailyalley.Entity.StoreEntity;
import likelionhackathon13.dailyalley.Entity.postEntity;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Repository.StoreRepository;
import likelionhackathon13.dailyalley.Repository.postRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class postService {
    private final StoreRepository storeRepository;
    private final postRepository postRepository;

    public void posttoai(postDto dto) throws Exception{
        Optional<StoreEntity> store = storeRepository.findById(dto.getStoreId());
            if(store.isEmpty()) throw new NotExistenceException();
            postEntity entity = postEntity
                    .builder()
                    .storeId(dto.getStoreId())
                    .info(dto.getInfo())
                    .hashtag(dto.getHashtag())
                    .tag(dto.getTag())
                    .picFeel(store.get().getPicFeel())
                    .postFeel(store.get().getPostFeel())
                    .createdDate(LocalDateTime.now())
                    .modifyDate(LocalDateTime.now())
                    .build();
            postRepository.save(entity);
    }

    public String aitopost(Long storeId) {
        if(storeRepository.findById(storeId).isEmpty()) throw new NotExistenceException();
        if(postRepository.findTopByStoreIdOrderByModifyDateDesc(storeId).isEmpty()) throw new RuntimeException();
        postEntity post = postRepository.findTopByStoreIdOrderByModifyDateDesc(storeId).get();
        return post.getBody();
    }
}