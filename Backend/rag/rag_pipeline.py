import os
import base64
from openai import OpenAI
from unstructured.partition.pdf import partition_pdf as unstructured_partition_pdf
from dotenv import load_dotenv
import os
import re
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def calculate_cost(input_tokens, output_tokens, model, cached_tokens=0):
    model_costs = {
    "gpt-4o":               {"input": 2.50,  "cached": 1.25,  "output": 10.00},
    "gpt-4o-mini":          {"input": 0.15,  "cached": 0.075, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02, "output": 0.00},
    "text-embedding-3-large": {"input": 0.13, "output": 0.00},}

    pricing = model_costs.get(model)
    if not pricing:
        return 0.0
    non_cached = input_tokens - cached_tokens
    input_cost  = (non_cached     / 1_000_000) * pricing["input"]
    cache_cost  = (cached_tokens  / 1_000_000) * pricing.get("cached", pricing["input"] * 0.5)
    output_cost = (output_tokens  / 1_000_000) * pricing["output"]
    return round(input_cost + cache_cost + output_cost, 8)


def is_useless_element(el) -> bool:
    text = str(el.text or "").strip()
    return (
        len(text) < 30 and el.category == "Image"  # tiny images are usually logos
        or text in ["", " "]
    )

def describe_image_with_vision(b64: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                },
                {
                    "type": "text",
                    "text": "Describe this image concisely for a RAG system. If it's a diagram or chart, explain what it shows. Wrap response in <image></image> tags. Explain freely"
                }
            ]
        }]
    )
    return {"content": response.choices[0].message.content, "input":response.usage.prompt_tokens , "output": response.usage.completion_tokens, "cached": response.usage.prompt_tokens_details.cached_tokens}

def partition_pdf_file(path: str) -> list:
    return unstructured_partition_pdf(
        filename=path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image", "Table"],  
        extract_image_block_to_payload=True
    )

def make_text(els) -> str:
    final_res = {"input": 0, "output":0, "cached": 0, "content": ""}
    for el in els:
        if is_useless_element(el):
            continue
        if el.category == "Image":
            if el.metadata.image_base64:
                output = describe_image_with_vision(el.metadata.image_base64)
                final_res["content"] += output["content"]
                final_res["input"] += output["input"]
                final_res["output"] += output["output"]
                final_res["cached"] += output["cached"]
        elif el.category == "Table":
            final_res["content"] += el.metadata.text_as_html or el.text
        else:
            final_res["content"] += el.text + "\n"
    return final_res

def agentic_chunk(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10000,
        messages=[{
            "role": "system",
            "content": "You are a document processing assistant. Split document text into semantic chunks for a RAG pipeline."
        }, {
            "role": "user",
            "content": f"""Split the following document text into semantic chunks by inserting <chunk> tags at boundaries.

Rules:
- Each chunk must be self-contained and answerable on its own
- Keep every question with ALL its related content: answers, tables, notes, exceptions, disclaimers
- Never split a table from its surrounding context or trailing "Note:"
- Skip decorative/useless content: logos, image descriptions, index pages, headers/footers
- Do NOT rewrite or paraphrase factual content — only remove filler words if needed
- Each chunk should answer at least one specific question a student might ask
- Wrap each chunk in <chunk> tags

Table handling:
- If a chunk contains a table, flatten it into natural language sentences inside <content>


Output format:
<chunk>
  <title>Short descriptive title</title>
<content>
    -Flattened natural language version of the content, no tables
    -Original markdown table (only if table exists)
</content>
</chunk>
Document:
{text}"""
        }]
    )
    print(f"Input tokens: {response.usage.prompt_tokens}")
    print(f"Output tokens: {response.usage.completion_tokens}")
    return {"content": response.choices[0].message.content, "input":response.usage.prompt_tokens , "output": response.usage.completion_tokens, "cached": response.usage.prompt_tokens_details.cached_tokens}

def get_embedding(text):
    try:
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        return {"input": response.usage.prompt_tokens,"output": 0,  "embedding": response.data[0].embedding}
    except Exception as e:
        print(e)
        return None

def rag(pdf_path: str = None, type_in: str = None, text_in: str = None, img_path=None):
    total_cost = {"input": 0, "output": 0, "cached": 0}
    chunked_text = None

    if type_in == "pdf":
        print(f"Partitioning: {pdf_path}")
        els = partition_pdf_file(pdf_path)

        print("Building text...")
        text = make_text(els)                          
        total_cost["input"]  += text["input"]
        total_cost["output"] += text["output"]
        total_cost["cached"] += text["cached"]

        print("Chunking...")
        chunked_text = agentic_chunk(text["content"])  
        total_cost["input"]  += chunked_text["input"]
        total_cost["output"] += chunked_text["output"]
        total_cost["cached"] += chunked_text["cached"]

    if type_in == "text":
        chunked_text = agentic_chunk(text_in)
        total_cost["input"]  += chunked_text["input"]
        total_cost["output"] += chunked_text["output"]
        total_cost["cached"] += chunked_text["cached"]

    if type_in == "image" and img_path:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        chunked_text = describe_image_with_vision(img_b64)
        total_cost["input"]  += chunked_text["input"]
        total_cost["output"] += chunked_text["output"]
        total_cost["cached"] += chunked_text["cached"]
    



    chunks = re.findall(r'<chunk>(.*?)</chunk>', chunked_text["content"], re.DOTALL)
    chunks = [c.strip() for c in chunks]
    embeddings = []
    embedding_cost = 0
    for chunk in chunks:
        res = get_embedding(chunk)
        embeddings.append(res["embedding"])
        total_cost["input"] += res["input"]
        embedding_cost += calculate_cost(res["input"], res["output"], "text-embedding-3-small")
    
    chunk_cost = calculate_cost(total_cost["input"], total_cost["output"], "gpt-4o-mini", total_cost["cached"])

    return {"chunks": chunks, "cost": chunk_cost + embedding_cost, "embeddings" : embeddings, "model": "text-embedding-3-small gpt-4o-mini", "tokens": total_cost}


