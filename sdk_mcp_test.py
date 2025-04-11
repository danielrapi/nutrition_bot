import asyncio
import os
import shutil
from dotenv import load_dotenv
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerStdio

load_dotenv()


async def run(mcp_server):
    agent = Agent(
        name="SupabaseAgent",
        instructions="You have access to a Supabase database. Use the tools to explore the schema and answer questions about the data.",
        mcp_servers=[mcp_server],
    )

    # Example query 1: list tables
    message = "List all the tables in the database for the project Nurity."
    print(f"Running: {message}")
    result = await Runner.run(agent, input=message)
    print(result.final_output)

    # Example query 2: infer schema
    message = "What does the users table contain for the project Nurity?"
    print(f"\n\nRunning: {message}")
    result = await Runner.run(agent, input=message)
    print(result.final_output)



async def main():
    # Replace this with your actual Supabase access token
    supabase_access_token = os.environ.get("SUPABASE_MCP_TOKEN", "<your_token_here>")

    if supabase_access_token == "<your_token_here>":
        raise ValueError("Please set your Supabase access token via SUPABASE_ACCESS_TOKEN")

    async with MCPServerStdio(
        name="Supabase Server (via npx)",
        params={
            "command": "npx",
            "args": [
                "-y",
                "@supabase/mcp-server-supabase",
                "--access-token",
                supabase_access_token
            ],
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="MCP Supabase Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)


if __name__ == "__main__":
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")
    asyncio.run(main())