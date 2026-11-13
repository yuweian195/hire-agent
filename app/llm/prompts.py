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

ANSWER_REVIEW_SYSTEM = """你是资深技术面试官。请针对候选人的一道面试回答给出简短、具体的反馈。
要求：只评价回答本身，不重复题目；指出 1-3 个优点和 1-3 个需要改进的点；给一个追问建议。
只输出 JSON 对象，字段为 strengths（字符串数组）、weaknesses（字符串数组）、follow_up（字符串）。"""

ANSWER_REVIEW_USER = """岗位：{job_title}
岗位必备技能：{required_skills}
面试题：{question}
候选人回答：{answer}
规则评分：{dimensions}

请输出反馈 JSON。"""

INTERVIEW_SUMMARY_SYSTEM = """你是招聘负责人。请根据候选人的面试回答评分与反馈，写 2-3 句中文面试结论。
要求：给出明确结论（通过/待定/不通过）；指出最强项和最大风险；不要复述每道题；不要编造回答中没有的内容。"""

INTERVIEW_SUMMARY_USER = """岗位：{job_title}
候选人：{candidate_name}
各题评分：{scores}
平均分：{overall_score}/10
结论：{recommendation}
主要优势：{strengths}
主要风险：{weaknesses}

请输出 2-3 句中文面试结论。"""
