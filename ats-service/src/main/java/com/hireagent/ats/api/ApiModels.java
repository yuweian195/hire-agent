package com.hireagent.ats.api;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public final class ApiModels {

    private ApiModels() {
    }

    public record JobResponse(
            String id,
            String title,
            String department,
            String seniority,
            Integer minYears,
            String education,
            List<String> requiredSkills,
            List<String> preferredSkills,
            String description
    ) {
    }

    public record CreateJobRequest(
            @NotBlank String id,
            @NotBlank String title,
            String department,
            String seniority,
            Integer minYears,
            String education,
            List<String> requiredSkills,
            List<String> preferredSkills,
            String description
    ) {
    }

    public record CandidateRequest(
            @NotBlank String name,
            String email,
            String phone,
            String source
    ) {
    }

    public record CandidateResponse(
            UUID id,
            String name,
            String email,
            String phone,
            String source,
            Instant createdAt
    ) {
    }

    public record ScreeningRequest(
            @NotBlank String candidateName,
            String candidateEmail,
            @NotBlank String jobId,
            @NotNull @DecimalMin("0") @DecimalMax("10") Double totalScore,
            @NotBlank String recommendation,
            @NotNull @DecimalMin("0") @DecimalMax("1") Double matchRate,
            String stage
    ) {
    }

    public record StageRequest(@NotBlank String stage) {
    }

    public record ScreeningResponse(
            UUID id,
            UUID candidateId,
            String candidateName,
            String candidateEmail,
            String jobId,
            String jobTitle,
            double totalScore,
            String recommendation,
            double matchRate,
            String stage,
            Instant createdAt
    ) {
    }

    public record HealthResponse(String status, String service, long jobs, long screenings) {
    }
}
