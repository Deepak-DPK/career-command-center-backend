# Career Command Center — CrewAI Optimization Guide

## Goal
Reduce Groq token usage while keeping **4 strong hackathon-worthy agents**.

---

## Problems in Current Architecture
Current backend uses:

- 7 agents
- 7 sequential tasks
- Long backstories (hundreds of tokens)
- `max_iter=25`
- Full resume + full JD sent to every agent

This causes:
- Groq rate limits
- Slow response
- High cost
- Render timeouts

---

# New Optimized Architecture (4 Agents)

## Agent 1 — Sleuth
**Role:** Resume Intelligence Specialist  
**Purpose:** Compare resume and JD, detect skill gaps, ATS score, missing keywords.

### Output
```json
{
  "skill_gaps": [],
  "missing_keywords": [],
  "ats_score": 82
}
```

---

## Agent 2 — Recruiter
**Role:** Hiring Manager Simulator  
**Purpose:** Generate realistic interview questions.

### Output
- 2 technical questions
- 2 behavioral questions
- 1 scenario question

---

## Agent 3 — Challenger
**Role:** Stress Interview Specialist  
**Purpose:** Generate:
- Pushback questions
- Salary negotiation questions

---

## Agent 4 — Coach
**Role:** Career Strategy Coach  
**Purpose:** Create final battle plan:
- Strengths
- Weaknesses
- STAR method
- Final preparation roadmap

---

# Remove These Agents

Delete completely:

- ATS Optimizer
- Salary Negotiator
- Outreach Strategist

Reason:
These do not need separate LLM agents.

---

# New agents.yaml

```yaml
---
sleuth:
  role: Resume Intelligence Specialist
  goal: Compare resume and job description to detect strengths, missing skills, and ATS gaps.
  backstory: Expert recruiter specializing in technical hiring.

recruiter:
  role: Hiring Manager Simulator
  goal: Create realistic interview questions tailored to the candidate and role.
  backstory: Senior engineering manager experienced in technical interviews.

challenger:
  role: Stress Interview Specialist
  goal: Generate hard pushback and salary negotiation questions targeting weak areas.
  backstory: Tough but fair interviewer skilled in exposing weak answers.

coach:
  role: Career Strategy Coach
  goal: Convert all insights into a concise interview battle plan with actionable advice.
  backstory: Elite interview coach for high-performing candidates.
```

---

# New tasks.yaml

```yaml
resume_analysis:
  description: |
    Analyze resume and job description.

    Resume:
    {resume_text}

    Job:
    {job_description}

    Return JSON:
    {
      "skill_gaps": [],
      "missing_keywords": [],
      "ats_score": number
    }
  agent: sleuth

interview_questions:
  description: |
    Generate exactly 5 interview questions:
    - 2 technical
    - 2 behavioral
    - 1 scenario
  agent: recruiter
  context:
    - resume_analysis

challenger_questions:
  description: |
    Generate:
    - 3 pushback questions
    - 3 salary negotiation questions
  agent: challenger
  context:
    - resume_analysis

coach_report:
  description: |
    Generate final report including:
    - strengths
    - weaknesses
    - STAR strategy
    - final preparation plan
  agent: coach
  context:
    - resume_analysis
    - interview_questions
    - challenger_questions
```

---

# crew.py Updates

## Remove Agent Functions
Delete:
- ATS optimizer agent
- Salary negotiator agent
- Outreach strategist agent

## Remove Task Functions
Delete:
- ats_optimization_analysis
- salary_negotiation_strategy
- generate_outreach_assets

## Reduce Iterations
Replace everywhere:

```python
max_iter=25
```

with:

```python
max_iter=3
```

---

# FastAPI Optimizations

Before sending to CrewAI:

```python
resume_text = resume_text[:3500]
job_description = job_description[:1800]
```

This reduces token usage drastically.

---

# Optional Hybrid Optimization (Recommended)

Use Python logic for ATS instead of LLM.

Example:

```python
resume_words = set(resume_text.lower().split())
jd_words = set(job_description.lower().split())
missing = list(jd_words - resume_words)
```

Benefits:
- Zero LLM tokens
- Faster ATS scoring

---

# Antigravity Prompt

Use this prompt in Antigravity:

```text
Refactor my CrewAI project for token efficiency.

Requirements:
1. Reduce architecture to exactly 4 agents:
   - Sleuth
   - Recruiter
   - Challenger
   - Coach

2. Remove these agents completely:
   - ATS Optimizer
   - Salary Negotiator
   - Outreach Strategist

3. Update agents.yaml and tasks.yaml accordingly.

4. Update crew.py:
   - Remove deleted agents/tasks
   - Change max_iter from 25 to 3
   - Preserve sequential execution

5. Add ATS optimization using pure Python instead of LLM.

6. Ensure final API response remains:
{
  "skill_gaps": [],
  "questions": [],
  "pushback_questions": [],
  "coach_report": ""
}

7. Optimize for Groq free tier and minimize token usage by 60%+.
```

---

.
