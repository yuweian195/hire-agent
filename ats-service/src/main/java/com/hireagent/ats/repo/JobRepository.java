package com.hireagent.ats.repo;

import com.hireagent.ats.domain.JobEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface JobRepository extends JpaRepository<JobEntity, String> {
}
