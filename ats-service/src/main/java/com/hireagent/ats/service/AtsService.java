package com.hireagent.ats.service;

import com.hireagent.ats.api.ApiModels.CandidateRequest;
import com.hireagent.ats.api.ApiModels.CandidateResponse;
import com.hireagent.ats.api.ApiModels.CreateJobRequest;
import com.hireagent.ats.api.ApiModels.JobResponse;
import com.hireagent.ats.api.ApiModels.ScreeningRequest;
import com.hireagent.ats.api.ApiModels.ScreeningResponse;
import com.hireagent.ats.domain.CandidateEntity;
import com.hireagent.ats.domain.JobEntity;
import com.hireagent.ats.domain.ScreeningRecordEntity;
import com.hireagent.ats.repo.CandidateRepository;
import com.hireagent.ats.repo.JobRepository;
import com.hireagent.ats.repo.ScreeningRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Service
public class AtsService {

    private static final Set<String> ALLOWED_STAGES =
            Set.of("screening", "interview", "offer", "rejected", "talent_pool");

    private final JobRepository jobs;
    private final CandidateRepository candidates;
    private final ScreeningRepository screenings;

    public AtsService(
            JobRepository jobs,
            CandidateRepository candidates,
            ScreeningRepository screenings
    ) {
        this.jobs = jobs;
        this.candidates = candidates;
        this.screenings = screenings;
    }

    @Transactional(readOnly = true)
    public List<JobResponse> listJobs() {
        return jobs.findAll().stream().map(this::toJobResponse).toList();
    }

    @Transactional
    public JobResponse createJob(CreateJobRequest request) {
        if (jobs.existsById(request.id())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "岗位已存在：" + request.id());
        }
        JobEntity entity = new JobEntity();
        entity.setId(request.id());
        entity.setTitle(request.title());
        entity.setDepartment(request.department());
        entity.setSeniority(request.seniority());
        entity.setMinYears(request.minYears() == null ? 0 : request.minYears());
        entity.setEducation(request.education() == null ? "本科" : request.education());
        entity.setRequiredSkills(request.requiredSkills() == null ? List.of() : request.requiredSkills());
        entity.setPreferredSkills(request.preferredSkills() == null ? List.of() : request.preferredSkills());
        entity.setDescription(request.description());
        return toJobResponse(jobs.save(entity));
    }

    @Transactional(readOnly = true)
    public List<CandidateResponse> listCandidates() {
        return candidates.findAll().stream().map(this::toCandidateResponse).toList();
    }

    @Transactional
    public CandidateResponse createCandidate(CandidateRequest request) {
        return toCandidateResponse(createOrGetCandidate(
                request.name(), request.email(), request.phone(), request.source()
        ));
    }

    @Transactional
    public ScreeningResponse createScreening(ScreeningRequest request) {
        JobEntity job = jobs.findById(request.jobId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "岗位不存在：" + request.jobId()));
        CandidateEntity candidate = createOrGetCandidate(
                request.candidateName(), request.candidateEmail(), null, "agent"
        );
        String stage = normalizeStage(request.stage());

        ScreeningRecordEntity entity = new ScreeningRecordEntity();
        entity.setCandidateId(candidate.getId());
        entity.setCandidateName(candidate.getName());
        entity.setCandidateEmail(candidate.getEmail());
        entity.setJobId(job.getId());
        entity.setJobTitle(job.getTitle());
        entity.setTotalScore(request.totalScore());
        entity.setRecommendation(request.recommendation());
        entity.setMatchRate(request.matchRate());
        entity.setStage(stage);
        entity.setCreatedAt(Instant.now());
        return toScreeningResponse(screenings.save(entity));
    }

    @Transactional(readOnly = true)
    public List<ScreeningResponse> listScreenings(String jobId) {
        List<ScreeningRecordEntity> result = jobId == null || jobId.isBlank()
                ? screenings.findAllByOrderByCreatedAtDesc()
                : screenings.findByJobIdOrderByCreatedAtDesc(jobId);
        return result.stream().map(this::toScreeningResponse).toList();
    }

    @Transactional
    public ScreeningResponse updateStage(UUID id, String stage) {
        ScreeningRecordEntity entity = screenings.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "筛选记录不存在"));
        entity.setStage(normalizeStage(stage));
        return toScreeningResponse(screenings.save(entity));
    }

    private CandidateEntity createOrGetCandidate(
            String name, String email, String phone, String source
    ) {
        if (email != null && !email.isBlank()) {
            return candidates.findByEmail(email).orElseGet(() -> {
                CandidateEntity entity = new CandidateEntity();
                entity.setName(name);
                entity.setEmail(email);
                entity.setPhone(phone);
                entity.setSource(source);
                return candidates.save(entity);
            });
        }
        CandidateEntity entity = new CandidateEntity();
        entity.setName(name);
        entity.setPhone(phone);
        entity.setSource(source);
        return candidates.save(entity);
    }

    private String normalizeStage(String stage) {
        String value = stage == null || stage.isBlank() ? "screening" : stage;
        if (!ALLOWED_STAGES.contains(value)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "非法流程状态：" + value);
        }
        return value;
    }

    private JobResponse toJobResponse(JobEntity entity) {
        return new JobResponse(
                entity.getId(),
                entity.getTitle(),
                entity.getDepartment(),
                entity.getSeniority(),
                entity.getMinYears(),
                entity.getEducation(),
                entity.getRequiredSkills(),
                entity.getPreferredSkills(),
                entity.getDescription()
        );
    }

    private CandidateResponse toCandidateResponse(CandidateEntity entity) {
        return new CandidateResponse(
                entity.getId(),
                entity.getName(),
                entity.getEmail(),
                entity.getPhone(),
                entity.getSource(),
                entity.getCreatedAt()
        );
    }

    private ScreeningResponse toScreeningResponse(ScreeningRecordEntity entity) {
        return new ScreeningResponse(
                entity.getId(),
                entity.getCandidateId(),
                entity.getCandidateName(),
                entity.getCandidateEmail(),
                entity.getJobId(),
                entity.getJobTitle(),
                entity.getTotalScore(),
                entity.getRecommendation(),
                entity.getMatchRate(),
                entity.getStage(),
                entity.getCreatedAt()
        );
    }
}
