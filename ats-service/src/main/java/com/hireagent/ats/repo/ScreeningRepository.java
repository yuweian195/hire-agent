package com.hireagent.ats.repo;

import com.hireagent.ats.domain.ScreeningRecordEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ScreeningRepository extends JpaRepository<ScreeningRecordEntity, UUID> {

    List<ScreeningRecordEntity> findAllByOrderByCreatedAtDesc();

    List<ScreeningRecordEntity> findByJobIdOrderByCreatedAtDesc(String jobId);
}
