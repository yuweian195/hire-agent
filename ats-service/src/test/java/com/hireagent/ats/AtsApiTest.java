package com.hireagent.ats;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AtsApiTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void seedsJobs() throws Exception {
        mockMvc.perform(get("/api/jobs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    void createsScreeningAndCandidate() throws Exception {
        String payload = """
                {
                  "candidateName": "张伟",
                  "candidateEmail": "zhangwei@example.com",
                  "jobId": "java-senior",
                  "totalScore": 9.13,
                  "recommendation": "recommend",
                  "matchRate": 0.98,
                  "stage": "screening"
                }
                """;

        MvcResult result = mockMvc.perform(post("/api/screenings")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.candidateName").value("张伟"))
                .andExpect(jsonPath("$.jobTitle").value("高级 Java 工程师"))
                .andExpect(jsonPath("$.recommendation").value("recommend"))
                .andReturn();

        JsonNode body = objectMapper.readTree(result.getResponse().getContentAsString());
        String screeningId = body.get("id").asText();
        assertThat(screeningId).isNotBlank();

        mockMvc.perform(get("/api/candidates"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("张伟"));

        mockMvc.perform(patch("/api/screenings/" + screeningId + "/stage")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"stage\":\"interview\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.stage").value("interview"));

        mockMvc.perform(get("/api/screenings").param("jobId", "java-senior"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(screeningId));
    }

    @Test
    void rejectsUnknownJob() throws Exception {
        String payload = """
                {
                  "candidateName": "测试候选人",
                  "jobId": "missing-job",
                  "totalScore": 7.0,
                  "recommendation": "hold",
                  "matchRate": 0.6
                }
                """;

        mockMvc.perform(post("/api/screenings")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isNotFound());
    }

    @Test
    void rejectsInvalidStage() throws Exception {
        mockMvc.perform(patch("/api/screenings/00000000-0000-0000-0000-000000000000/stage")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"stage\":\"invalid\"}"))
                .andExpect(status().isNotFound());
    }

    @Test
    void healthReportsCounts() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ok"))
                .andExpect(jsonPath("$.jobs").value(2));
    }
}
