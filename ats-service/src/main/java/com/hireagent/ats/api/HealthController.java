package com.hireagent.ats.api;

import com.hireagent.ats.api.ApiModels.HealthResponse;
import com.hireagent.ats.repo.JobRepository;
import com.hireagent.ats.repo.ScreeningRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class HealthController {

    private final JobRepository jobs;
    private final ScreeningRepository screenings;

    public HealthController(JobRepository jobs, ScreeningRepository screenings) {
        this.jobs = jobs;
        this.screenings = screenings;
    }

    @GetMapping("/health")
    public HealthResponse health() {
        return new HealthResponse("ok", "ats-service", jobs.count(), screenings.count());
    }
}
