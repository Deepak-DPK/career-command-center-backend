import os
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_llm():
    """
    Returns the Groq Llama 3.1 8B LLM (configured for Free Tier limits). Raises an error if GROQ_API_KEY is not defined.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("CRITICAL: GROQ_API_KEY environment variable is not configured in the environment.")
    return LLM(
        model=os.getenv("MODEL_NAME", "groq/llama-3.1-8b-instant"),
        api_key=groq_api_key,
        temperature=0.3
    )

@CrewBase
class CareerCommandCenterCrew:
    """CareerCommandCenter crew"""

    @agent
    def sleuth(self) -> Agent:
        return Agent(
            config=self.agents_config["sleuth"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=3,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def recruiter(self) -> Agent:
        return Agent(
            config=self.agents_config["recruiter"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=3,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def challenger(self) -> Agent:
        return Agent(
            config=self.agents_config["challenger"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=3,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @agent
    def coach(self) -> Agent:
        return Agent(
            config=self.agents_config["coach"],
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=3,
            max_rpm=None,
            max_execution_time=None,
            llm=get_llm(),
        )

    @task
    def resume_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["resume_analysis"],
            markdown=False,
        )

    @task
    def interview_questions(self) -> Task:
        return Task(
            config=self.tasks_config["interview_questions"],
            markdown=False,
        )

    @task
    def challenger_questions(self) -> Task:
        return Task(
            config=self.tasks_config["challenger_questions"],
            markdown=False,
        )

    @task
    def coach_report(self) -> Task:
        return Task(
            config=self.tasks_config["coach_report"],
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
