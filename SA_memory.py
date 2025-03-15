from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import json

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.pretty import pprint
from phi.storage.agent.sqlite import SqlAgentStorage


web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-1.5-flash"),
    storage=SqlAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
    add_history_to_messages=True,
    num_history_responses=3,
    session_id="8074104c-4600-490d-9e79-36e82a03d215",
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True,
)

console = Console()


def print_chat_history(agent):
    # -*- Print history
    console.print(
        Panel(
            JSON(json.dumps([m.model_dump(include={"role", "content"}) for m in agent.memory.messages]), indent=4),
            title=f"Chat History for session_id: {agent.session_id}",
            expand=True,
        )
    )


# # -*- Create a run
# web_agent.print_response("what is story?", stream=True)
# -*- Print the chat history
print_chat_history(web_agent)

# -*- Ask a follow up question that continues the conversation
web_agent.print_response("can i create it?", stream=True)
# -*- Print the chat history
print_chat_history(web_agent)