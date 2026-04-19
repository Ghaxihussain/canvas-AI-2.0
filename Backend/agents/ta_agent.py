import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Backend.services.aws import get_s3_object
import sys
import os
from dotenv import load_dotenv
load_dotenv()
import base64
from openai import OpenAI
import json
from sqlalchemy import text
from Backend.db.database import SessionLocal
import re
from sqlalchemy import text
client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))



def check_hw(assignment_key, submission_key, rubric_key=None, rubric_text=None, total_grade=100):
    
    def build_content_block(data: bytes, content_type: str, label: str) -> list:
        
        blocks = [{"type": "text", "text": f"--- {label} ---"}]
        
        if content_type.startswith("text/"):
            blocks.append({"type": "text", "text": data.decode("utf-8")})
        
        elif content_type.startswith("image/"):
            b64 = base64.b64encode(data).decode("utf-8")
            blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:{content_type};base64,{b64}"}
            })
        
        elif content_type == "application/pdf":
            b64 = base64.b64encode(data).decode("utf-8")
            blocks.append({
                "type": "file",
                "file": {
                    "filename": f"{label}.pdf",
                    "file_data": f"data:application/pdf;base64,{b64}"
                }
            })
        
        return blocks
    rubric = []
    
    if rubric_key is None and rubric_text is None:
        rubric = [{"type": "text", "text": "--- RUBRIC ---\nCHECK THIS BASED ON YOUR KNOWLEDGE"}]
   

    if rubric_key is not None:
        rubric_data, rubric_content_type = get_s3_object(os.getenv("AWS_BUCKET_NAME"), rubric_key)
        rubric += build_content_block(rubric_data, rubric_content_type, "RUBRIC FILE")

    if rubric_text is not None:
        rubric += [{"type": "text", "text": f"--- RUBRIC TEXT ---\n{rubric_text}"}]

    assignment_data, assignment_content_type = get_s3_object(os.getenv("AWS_BUCKET_NAME"), assignment_key)
    submission_data, submission_content_type = get_s3_object(os.getenv("AWS_BUCKET_NAME"), submission_key)

    assignment_blocks = build_content_block(assignment_data, assignment_content_type, "ASSIGNMENT")
    submission_blocks = build_content_block(submission_data, submission_content_type, "SUBMISSION")

    system_prompt = f"""You are a strict but fair homework grader.
Grade the student's submission against the assignment and rubric.
If you are unable to check or grade the assignment for any reason 
(unreadable file, unclear submission, missing content, etc.), respond with exactly one word: utca
Total grade is out of {total_grade} points.
Return your response in this format:
- Score: X/{total_grade}
- Feedback: <detailed feedback>
- Breakdown: <per-section or per-question scores if applicable>
"""

    content = [
        *rubric,
        *assignment_blocks,
        *submission_blocks,
        {"type": "text", "text": f"Now grade the submission out of {total_grade} points."}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    )

    return response.choices[0].message.content


def sql_query_genrator(query):
    structure = None
    with open("Backend/db_structure.json") as c:
        structure = json.load(c)
    prompt = f"""You are a SQL agent. Generate only valid SQL queries.
The database is PostgreSQL with this schema:

<schema>
  {structure}
</schema>

Rules:
- Only return the SQL query, no explanation
- Use table aliases for joins
- Never use SELECT *
- You are not allowed to delete any row, column or table
- You are not allowed to update any row, column or table

Return ONLY the raw SQL query with no explanation, 
no markdown, no code fences, no preamble."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
            
        ]
    ,temperature=0
    )
    return response.choices[0].message.content




def extract_sql(raw: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw.strip()



def is_write_query(sql: str) -> bool:
    pattern = r'\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE)\b'
    return bool(re.search(pattern, sql, re.IGNORECASE))

def excecute_sql(query):
    sql_raw = sql_query_genrator(query)
    sql = extract_sql(sql_raw)
    
    if is_write_query(sql):
        return None
    
    try:
        with SessionLocal() as db:
            result = db.execute(text(sql))
            rows = result.fetchall()
            keys = result.keys()
 
    except Exception as e:               
        raise RuntimeError(f"Unexpected error: {e}") from e
    

    return {"result": [dict(zip(keys, row)) for row in rows], "sql": sql}



if __name__ == "__main__":
    print(excecute_sql("What is the min and max marks a person has scored in any of the graded submission"))