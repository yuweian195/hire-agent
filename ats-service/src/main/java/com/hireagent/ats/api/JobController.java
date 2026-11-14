package com.hireagent.ats.api;

import com.hireagent.ats.api.ApiModels.CreateJobRequest;
import com.hireagent.ats.api.ApiModels.JobResponse;
import com.hireagent.ats.service.AtsService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/jobs")
public class JobController {

    private final AtsService service;

    public JobController(AtsService service) {
        this.service = service;
    }

    @GetMapping
    public List<JobResponse> list() {
        return service.listJobs();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public JobResponse create(@Valid @RequestBody CreateJobRequest request) {
        return service.createJob(request);
    }
}
