package likelionhackathon13.dailyalley.Repository;

import likelionhackathon13.dailyalley.Entity.postEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface postRepository extends JpaRepository<postEntity, Long> {
    Optional<postEntity> findTopByStoreIdOrderByModifyDateDesc(Long storeId);
}