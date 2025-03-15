from phi.agent import Agent
from phi.model.google import Gemini
from phi.embedder.google import GeminiEmbedder
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.vectordb.lancedb import LanceDb,SearchType


knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://courses.edx.org/asset-v1:Databricks+LLM101x+2T2023+type@asset+block@Module_2_slides.pdf"],
    vector_db=LanceDb(
        table_name="VectorDB",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=GeminiEmbedder(),
        ),
)

knowledge_base.load()

retrieval_agent= Agent(
    model=Gemini(id="gemini-1.5-flash"),
    description="you help user by answering the question",
    instructions="Answer the questions as detail as possible",
    knowledge=knowledge_base,
    search_knowledge=True,
    show_tool_calls=True,
    markdown=True,
)

retrieval_agent.knowledge.load(recreate=False)

retrieval_agent.print_response("Explain embedding of data", stream=True)

