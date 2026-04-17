from openai import OpenAI
from Backend.rag.rag_pipeline import rag
from dotenv import load_dotenv
from Backend.db.ragstore import RagStore
from Backend.db.api_costs import APICost
from Backend.db.database import SessionLocal
import os
import json
load_dotenv()
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


rag_agent_client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))

def search_vdb(query):
    try:
        with SessionLocal() as db:
            results = RagStore.search(query=query, class_id = "c59597b2-5209-47f3-ab3c-42b456dc3a88", db = db, top_k= 10) # need some changes here   this is hard coded 
        return results
    
    except Exception as e:
        print(e)
        return None

def clear_query(query):
    response = rag_agent_client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10000,
        messages=[
            {"role": "system", "content": "Rewrite the user's query into a clear, specific search query optimized for semantic similarity search. Keep it concise and preserve the original intent."},
            {"role": "user", "content": query}
        ]
    )
    return {"content": response.choices[0].message.content}


def rag_agent_main(prompt: str):

    api_cost_info = {"input": 0, "output" : 0}
    embedding_cost_info = {"input": 0}


    with open("Backend/agents/rag_agent_tools.json") as j:
        tools = json.load(j)

    messages = [
        {"role": "system", "content": "You are a course assistant. You ONLY answer from the vector database search results. If the search returns no relevant information, say 'I could not find this in the course materials.' NEVER use your training knowledge to answer questions."},
        {"role": "user", "content" : prompt}
    ]
    i = 0
    while True:
        print("Agent working ...... ")
        response = rag_agent_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools
        )
        choice  = response.choices[0]

        api_cost_info["input"] += response.usage.prompt_tokens
        api_cost_info["output"] += response.usage.completion_tokens

        if choice.finish_reason == "tool_calls":
            print("tool called .......")
            tool_call = choice.message.tool_calls[0]
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if name == "search_vdb":
                print("searching vector db ....... ")
                chunks = search_vdb(args["query"])
                if not chunks:
                    return "No chunks found"
                result = "\n\n".join([chunk.content for chunk in chunks["results"]])
                embedding_cost_info["input"] += chunks["input"]
            else:
                result = f"Unknown tool: {name}"

            messages.append(choice.message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
        
        elif choice.finish_reason == "stop":

            total_cost = APICost.calculate_cost(input_tokens= embedding_cost_info["input"], output_tokens= 0, model = "text-embedding-3-small") + APICost.calculate_cost(input_tokens= api_cost_info["input"], output_tokens= api_cost_info["output"], model = "gpt-4o")
            print("Total Cost  :- ", total_cost)
            with SessionLocal() as db:
                APICost.create(
                    db=db,
                    user_id="5f7ed410-9a4c-42c4-8731-107d732268bc", ## this also needs a change, this is hardcoded
                    model= "gpt-4o text-embedding-3-small",
                    endpoint="/test/rag/upload",
                    input_tokens= embedding_cost_info["input"] + api_cost_info["input"],
                    output_tokens=api_cost_info["output"],
                    cached_tokens=0,
                    cost= total_cost
                )
                print("Cost logged")
            return choice.message.content
        i += 1

        if i == 100:
            return "100 iter completed"
        




if __name__ == "__main__":
    while True:
        ui = input("Enter your query: ")
        if ui.lower() == "exit":
            break
        response = rag_agent_main(ui)
        print("Agent Response: ", response)