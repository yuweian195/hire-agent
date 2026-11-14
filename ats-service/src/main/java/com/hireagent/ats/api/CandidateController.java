package com.hireagent.ats.api;

import com.hireagent.ats.api.ApiModels.CandidateRequest;
import com.hireagent.ats.api.ApiModels.CandidateResponse;
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
@RequestMapping("/api/candidates")
public class CandidateController {

    private final AtsService service;

    public CandidateController(AtsService service) {
        this.service = service;
    }

    @GetMapping
    public List<CandidateResponse> list() {
        return service.listCandidates();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CandidateResponse create(@Valid @RequestBody CandidateRequest request) {
        return service.createCandidate(request);
    }
}
