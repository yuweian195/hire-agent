package com.hireagent.ats.api;

import com.hireagent.ats.api.ApiModels.ScreeningRequest;
import com.hireagent.ats.api.ApiModels.ScreeningResponse;
import com.hireagent.ats.api.ApiModels.StageRequest;
import com.hireagent.ats.service.AtsService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/screenings")
public class ScreeningController {

    private final AtsService service;

    public ScreeningController(AtsService service) {
        this.service = service;
    }

    @GetMapping
    public List<ScreeningResponse> list(@RequestParam(required = false) String jobId) {
        return service.listScreenings(jobId);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ScreeningResponse create(@Valid @RequestBody ScreeningRequest request) {
        return service.createScreening(request);
    }

    @PatchMapping("/{id}/stage")
    public ScreeningResponse updateStage(
            @PathVariable UUID id,
            @Valid @RequestBody StageRequest request
    ) {
        return service.updateStage(id, request.stage());
    }
}
