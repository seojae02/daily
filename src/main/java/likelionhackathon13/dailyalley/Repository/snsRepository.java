package likelionhackathon13.dailyalley.Repository;

import likelionhackathon13.dailyalley.Entity.snsEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface snsRepository extends JpaRepository<snsEntity, String> {

    Optional<snsEntity> findByStoreId(Long storeId);
}