package likelionhackathon13.dailyalley.Repository;

import likelionhackathon13.dailyalley.Entity.imgEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface imgRepository extends JpaRepository<imgEntity, String> {
    List<imgEntity> findAllByStoreId(long storeId);
    Optional<imgEntity> findByUrl(String url);
}
