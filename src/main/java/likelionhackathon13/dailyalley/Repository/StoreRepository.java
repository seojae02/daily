package likelionhackathon13.dailyalley.Repository;

import likelionhackathon13.dailyalley.Entity.StoreEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StoreRepository extends JpaRepository<StoreEntity, Long> {
}
