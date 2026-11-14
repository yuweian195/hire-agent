package com.hireagent.ats.config;

import com.hireagent.ats.domain.JobEntity;
import com.hireagent.ats.repo.JobRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class DataSeeder {

    @Bean
    CommandLineRunner seedJobs(JobRepository jobs) {
        return args -> {
            if (jobs.count() > 0) {
                return;
            }
            JobEntity javaRole = new JobEntity();
            javaRole.setId("java-senior");
            javaRole.setTitle("高级 Java 工程师");
            javaRole.setDepartment("交易技术部");
            javaRole.setSeniority("高级");
            javaRole.setMinYears(5);
            javaRole.setEducation("本科");
            javaRole.setRequiredSkills(List.of(
                    "Java", "Spring Boot", "Spring Cloud", "MySQL", "Redis", "Kafka", "微服务"
            ));
            javaRole.setPreferredSkills(List.of("Docker", "Kubernetes", "高并发", "分布式事务"));
            javaRole.setDescription("负责交易中台核心服务、分布式系统设计与高并发治理。");

            JobEntity aiRole = new JobEntity();
            aiRole.setId("llm-app");
            aiRole.setTitle("AI 应用工程师（LLM）");
            aiRole.setDepartment("智能应用部");
            aiRole.setSeniority("中级");
            aiRole.setMinYears(3);
            aiRole.setEducation("本科");
            aiRole.setRequiredSkills(List.of(
                    "Python", "FastAPI", "LangGraph", "RAG", "向量数据库", "Prompt Engineering"
            ));
            aiRole.setPreferredSkills(List.of("Docker", "Kubernetes", "LLM", "评测"));
            aiRole.setDescription("负责企业知识库问答、文档审查等 Agent 产品落地。");

            jobs.saveAll(List.of(javaRole, aiRole));
        };
    }
}
