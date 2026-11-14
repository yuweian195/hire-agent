export type Stage = "screening" | "interview" | "offer" | "rejected" | "talent_pool";
export type Recommendation = "recommend" | "hold" | "reject";

export interface ScreeningItem {
  id: string;
  candidate_name: string;
  job_id: string;
  job_title: string;
  total_score: number;
  recommendation: Recommendation;
  match_rate: number;
  stage: Stage;
  created_at: string;
}

export interface DimensionScore {
  key: string;
  label: string;
  score: number;
  weight: number;
  reason: string;
}

export interface SkillMatch {
  overall_rate: number;
  required_rate: number;
  preferred_rate: number;
  matched: string[];
  missing: string[];
}

export interface JobMatch {
  overall_rate: number;
  skill_rate: number;
  experience_rate: number;
  education_rate: number;
  analysis: string;
}

export interface InterviewQuestion {
  category: string;
  question: string;
  intent: string;
  difficulty: string;
}

export interface TraceStep {
  node: string;
  label: string;
  status: string;
  duration_ms: number;
  summary: string;
}

export interface ScreeningDetail extends ScreeningItem {
  recommendation_reason: string;
  summary: string;
  dimension_scores: DimensionScore[];
  skill_match: SkillMatch;
  job_match: JobMatch;
  questions: InterviewQuestion[];
  trace: TraceStep[];
  parsed_resume: {
    name: string;
    education_level: string;
    school: string;
    years_experience: number;
    skills: string[];
  };
}
