from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from phi.playground import Playground, serve_playground_app

web_agent = Agent(
    name="Web Agent",
    model=Gemini(id="gemini-1.5-flash"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True,
)

app = Playground(agents=[web_agent]).get_app(use_async=False)

if __name__ == "__main__":
    serve_playground_app("searchAgent:app", reload=True)