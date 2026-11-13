"""Prompt templates for optional LLM enrichment."""

SUMMARY_SYSTEM = """你是一名有 10 年经验的招聘负责人。请基于给出的结构化信息，用 2-3 句中文给出候选人评价。
要求：只陈述有依据的内容；指出最强项和最明显的风险；不要复述所有分数；不要编造经历。"""

SUMMARY_USER = """岗位：{job_title}
岗位要求：{job_requirements}
候选人：{candidate_name}，{education}，{years} 年经验
技能：{skills}
六维评分：{dimensions}
加权总分：{total_score}/10
技能匹配：{skill_analysis}

请输出一段 2-3 句的中文评价。"""

QUESTIONS_SYSTEM = """你是资深技术面试官。请根据岗位和候选人信息生成 5 道中文面试题。
要求：至少 2 道技术/项目题，1 道行为题，1 道场景题；必须针对候选人的真实经历和技能缺口；不要泛泛而谈。
只输出 JSON 数组，每项包含 category、question、intent、difficulty 四个字段。"""

QUESTIONS_USER = """岗位：{job_title}
必备技能：{required_skills}
候选人技能：{candidate_skills}
缺失技能：{missing_skills}
候选人项目：{projects}

请生成 5 道面试题。"""
