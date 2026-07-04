import os
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_llm():
    """
    Returns the Groq Llama 3.3 70B LLM. Raises an error if GROQ_API_KEY is not defined.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("CRITICAL: GROQ_API_KEY environment variable is not configured in the environment.")
    return LLM(
        model=os.getenv("MODEL_NAME", "groq/llama-3.3-70b-versatile"),
        api_key=groq_api_key,
        temperature=0.3
    )

@CrewBase
class CareerCommandCenterCrew:
    """CareerCommandCenter crew"""

    @agent
    def the_sleuth___resume_analyzer_and_skill_gap_detector(self) -> Agent:
        return Agent(
            config=self.agents_config["the_sleuth___resume_analyzer_and_skill_gap_detector"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_recruiter___hiring_manager_simulator(self) -> Agent:
        return Agent(
            config=self.agents_config["the_recruiter___hiring_manager_simulator"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_red_teamer___stress_interviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["the_red_teamer___stress_interviewer"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_coach___interview_mentor_and_strategy_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["the_coach___interview_mentor_and_strategy_architect"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_ats_optimizer___applicant_tracking_system_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["the_ats_optimizer___applicant_tracking_system_specialist"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_salary_negotiator___hr_compensation_strategy_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["the_salary_negotiator___hr_compensation_strategy_specialist"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def the_outreach_strategist___networking_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["the_outreach_strategist___networking_specialist"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @task
    def resume_gap_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["resume_gap_analysis"],
            markdown=False,
        )

    @task
    def ats_optimization_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["ats_optimization_analysis"],
            markdown=False,
        )

    @task
    def generate_interview_questions(self) -> Task:
        return Task(
            config=self.tasks_config["generate_interview_questions"],
            markdown=False,
        )

    @task
    def generate_pushback_questions(self) -> Task:
        return Task(
            config=self.tasks_config["generate_pushback_questions"],
            markdown=False,
        )

    @task
    def salary_negotiation_strategy(self) -> Task:
        return Task(
            config=self.tasks_config["salary_negotiation_strategy"],
            markdown=False,
        )

    @task
    def generate_outreach_assets(self) -> Task:
        return Task(
            config=self.tasks_config["generate_outreach_assets"],
            markdown=False,
        )

    @task
    def generate_interview_coaching_report(self) -> Task:
        return Task(
            config=self.tasks_config["generate_interview_coaching_report"],
            markdown=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CareerCommandCenter crew"""
        # Dynamically load knowledge sources for RAG context
        knowledge_sources = []
        knowledge_dir = "knowledge"
        if os.path.exists(knowledge_dir):
            txt_files = [os.path.join(knowledge_dir, f) for f in os.listdir(knowledge_dir) if f.endswith(".txt")]
            if txt_files:
                try:
                    text_source = TextFileKnowledgeSource(file_paths=txt_files)
                    knowledge_sources.append(text_source)
                except Exception as e:
                    print(f"Warning: Failed to load text knowledge sources: {e}")

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            chat_llm=get_llm(),
            knowledge_sources=knowledge_sources if knowledge_sources else None,
        )
