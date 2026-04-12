import os
import base64
from openai import OpenAI
from unstructured.partition.pdf import partition_pdf as unstructured_partition_pdf
from dotenv import load_dotenv
import os
import re
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    return response.choices[0].message.content

def partition_pdf_file(path: str) -> list:
    return unstructured_partition_pdf(
        filename=path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image", "Table"],  
        extract_image_block_to_payload=True
    )

def make_text(els) -> str:
    res = ""
    for el in els:
        if is_useless_element(el):
            continue
        if el.category == "Image":
            if el.metadata.image_base64:
                res += describe_image_with_vision(el.metadata.image_base64)
        elif el.category == "Table":
            res += el.metadata.text_as_html or el.text
        else:
            res += el.text + "\n"
    return res

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
    return response.choices[0].message.content

def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def rag(pdf_path: str = None, type_in: str = None, text_in: str = None, img_path = None):
    chunked_text = None
    if type_in == "pdf":
        print(f"Partitioning: {pdf_path}")
        els = partition_pdf_file(pdf_path)
        
        print("Building text...")
        text = make_text(els)
        print("Chunking...")
        chunked_text = agentic_chunk(text)
    
    if type_in == "text":
        chunked_text = agentic_chunk(text_in)
    


    if type_in == "image" and img_path:
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        chunked_text = describe_image_with_vision(img_b64)


    chunks = re.findall(r'<chunk>(.*?)</chunk>', chunked_text, re.DOTALL)
    chunks = [c.strip() for c in chunks]

    
    return chunks


