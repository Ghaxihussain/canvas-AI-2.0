import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from Backend.rag.rag_pipeline import rag
from Backend.db.ragstore import RagStore
from Backend.db.api_costs import APICost
from Backend.db.database import SessionLocal


class RAGAgent:

    SYSTEM_PROMPT = """You are a course assistant. You ONLY answer from the vector database search results.
        If the search returns no relevant information, say 'I could not find this in the course materials.'
        NEVER use your training knowledge to answer questions."""

    MAX_ITERATIONS = 100

    def __init__(self, class_id: str, user_id: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.class_id = class_id
        self.user_id = user_id

        with open("Backend/agents/rag_agent_tools.json") as f:
            self.tools = json.load(f)

    def search_vdb(self, query: str):
        try:
            with SessionLocal() as db:
                results = RagStore.search(query=query, class_id=self.class_id, db=db, top_k=10)
            return results
        except Exception as e:
            print(f"VDB search error: {e}")
            return None

    def clear_query(self, query: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10000,
            messages=[
                {"role": "system", "content": "Rewrite the user's query into a clear, specific search query optimized for semantic similarity search. Keep it concise and preserve the original intent."},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content

    def log_cost(self, api_tokens: dict, embedding_tokens: dict):
        total_cost = (
            APICost.calculate_cost(input_tokens=embedding_tokens["input"], output_tokens=0, model="text-embedding-3-small") +
            APICost.calculate_cost(input_tokens=api_tokens["input"], output_tokens=api_tokens["output"], model="gpt-4o")
        )
        print("Total Cost:", total_cost)

        with SessionLocal() as db:
            APICost.create(
                db=db,
                user_id=self.user_id,
                model="gpt-4o text-embedding-3-small",
                endpoint="/test/rag/upload",
                input_tokens=embedding_tokens["input"] + api_tokens["input"],
                output_tokens=api_tokens["output"],
                cached_tokens=0,
                cost=total_cost
            )
        print("Cost logged")

    def run(self, prompt: str) -> str:
        api_tokens = {"input": 0, "output": 0}
        embedding_tokens = {"input": 0}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        for i in range(self.MAX_ITERATIONS):
            print("Agent working...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools
            )
            choice = response.choices[0]

            api_tokens["input"] += response.usage.prompt_tokens
            api_tokens["output"] += response.usage.completion_tokens

            if choice.finish_reason == "tool_calls":
                print("Tool called...")
                messages.append(choice.message)

                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if name == "search_vdb":
                        print("Searching vector DB...")
                        chunks = self.search_vdb(args["query"])
                        if not chunks:
                            return "No chunks found"
                        result = "\n\n".join([chunk.content for chunk in chunks["results"]])
                        embedding_tokens["input"] += chunks["input"]
                    else:
                        result = f"Unknown tool: {name}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })

            elif choice.finish_reason == "stop":
                self.log_cost(api_tokens, embedding_tokens)
                return choice.message.content

        return "Max iterations reached"


