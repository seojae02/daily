package likelionhackathon13.dailyalley.Service;

import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MinioClient;
import io.minio.http.Method;
import likelionhackathon13.dailyalley.Dto.imgDto;
import likelionhackathon13.dailyalley.Entity.imgEntity;
import likelionhackathon13.dailyalley.Exception.DuplicatenameException;
import likelionhackathon13.dailyalley.Exception.NotExistenceException;
import likelionhackathon13.dailyalley.Exception.NotExistencenameException;
import likelionhackathon13.dailyalley.Repository.StoreRepository;
import likelionhackathon13.dailyalley.Repository.imgRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class imgService {
    private final MinioClient minioClient;
    private final StoreRepository storeRepository;
    private final imgRepository imgRepository;

    @Value("${minio.bucket}")
    private String Bucket;

    public String putimg(long storeId, String name) throws Exception {
        if(storeRepository.findById(storeId).isEmpty()) throw new NotExistenceException();
        if(imgRepository.findById(name).isPresent() && storeRepository.findById(storeId).isPresent()) throw new DuplicatenameException("이미 존재하는 이름입니다");
        String url = minioClient.getPresignedObjectUrl(
                GetPresignedObjectUrlArgs
                        .builder()
                        .method(Method.PUT)
                        .bucket(Bucket)
                        .object(storeId + "_" + name)
                        .expiry(10, TimeUnit.MINUTES)
                        .build()
        );
        imgEntity entity = imgEntity.builder()
                .name(name)
                .storeId(storeId)
                .url(url)
                .createDate(LocalDateTime.now())
                .modifyDate(LocalDateTime.now())
                .build();
        imgRepository.save(entity);
        return url;
    }

    public String getimg(long storeId, String name) throws Exception {
        if(storeRepository.findById(storeId).isEmpty()) throw new NotExistenceException();
        if(imgRepository.findById(name).isEmpty()) throw new NotExistencenameException("존재하지 않는 name입니다.");
        String url = minioClient.getPresignedObjectUrl(
                GetPresignedObjectUrlArgs
                        .builder()
                        .method(Method.GET)
                        .bucket(Bucket)
                        .object(storeId + "_" + name)
                        .expiry(10, TimeUnit.MINUTES)
                        .build()
        );
        imgEntity entity = imgRepository.findById(name).get();
        entity.setModifyDate(LocalDateTime.now());
        entity.setUrl(url);
        imgRepository.save(entity);
        return url;
    }

    public List<imgDto> getallimg(long storeId) throws Exception {
        if(storeRepository.findById(storeId).isEmpty()) throw new NotExistenceException();
        List<imgEntity> entityList = imgRepository.findAllByStoreId(storeId);
        entityList.forEach(img -> {
            try {
                String url = minioClient.getPresignedObjectUrl(
                        GetPresignedObjectUrlArgs.builder()
                                .method(Method.GET)
                                .bucket(Bucket)
                                .object(storeId + "_" + img.getName())
                                .expiry(10, TimeUnit.MINUTES)
                                .build()
                );
                img.setUrl(url);
                img.setModifyDate(LocalDateTime.now());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
        updateUrls(entityList);
        return entityList.stream().map(img -> new imgDto(img.getName(), img.getUrl())).toList();
    }

    public String getimgfurl(String url) throws Exception {
        imgEntity entity = imgRepository.findByUrl(url).get();
        if(imgRepository.findByUrl(url).isEmpty()) throw new NotExistencenameException("존재하지 않거나 이미 바뀐 url입니다.");
        return entity.getStoreId() + "_" + entity.getName();
    }

    @Transactional
    public void updateUrls(List<imgEntity> list) {
        list.forEach(img -> img.setModifyDate(LocalDateTime.now()));
        imgRepository.saveAll(list);
    }
}
