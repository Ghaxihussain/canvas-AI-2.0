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
from sqlalchemy import Update, select
from Backend.db.submissions import Submission
from Backend.db.assignments import Assignment
from pydantic import BaseModel, Field

class GradeResponse(BaseModel):
    grade: float = Field(description="the score of the student out of total grade")
    feedback: str = Field(description="detailed feedback for the student")

client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))

structure = None
tools = None
with open("Backend/agents/ta_agent_tools.json") as filehandle:
    tools = json.load(filehandle)
with open("Backend/db_structure.json") as c:
    structure = json.load(c)

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
"""

    content = [
        *rubric,
        *assignment_blocks,
        *submission_blocks,
        {"type": "text", "text": f"Now grade the submission out of {total_grade} points."}
    ]

    response = client.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        response_format= GradeResponse
    )

    return response.choices[0].message.parsed




def sql_query_genrator(query):
    
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

def get_data_from_db(query):
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

def assignment_id_based_homework_checker(aid):
    try:
        with SessionLocal() as db:
            assignment = db.execute(select(Assignment).where(Assignment.id == aid)).scalar_one_or_none()
            submissions = db.execute(select(Submission).where(Submission.assignment_id == aid)).scalars().all()

            print("checking assignment ......")
            for submission in submissions:
                res = check_hw(submission_key=submission.file_url, assignment_key= assignment.assignment_file_url, rubric_text= assignment.rubric_text_content, rubric_key= assignment.rubric_file_url)
                Submission.grade_submission(assignment_id=aid, user_id = submission.user_id, grade = res.grade, feedback = f"This is a AI genrated Feedback \n{res.feedback}", db = db)
        return True

    except Exception as e:
        print(f"error {e}")
        return False

        
def submission_number_based_homework_checker(sid):
    try:
        with SessionLocal() as db:
            submission = db.execute(select(Submission).where(Submission.assignment_id == sid)).scalar_one_or_none()
            assignment = db.execute(select(Assignment).where(Assignment.id == submission.assignment_id)).scalar_one_or_none()
            print("checking assignment ......")
            res = check_hw(submission_key=submission.file_url, assignment_key= assignment.assignment_file_url, rubric_text= assignment.rubric_text_content, rubric_key= assignment.rubric_file_url)
            Submission.grade_submission(assignment_id=sid, user_id = submission.user_id, grade = res.grade, feedback = f"This is a AI genrated Feedback \n{res.feedback}", db = db)
        return True

    except Exception as e:
        print(f"error {e}")
        return False

system_prompt = """You are a TA (Teaching Assistant) AI agent for a Canvas-like learning management system.
You have access to tools to query the database and grade student submissions.

## Your Responsibilities
- Answer questions about assignments, submissions, and grades
- Grade submissions when asked
- Generate reports on student performance
- Query the database to retrieve accurate information

## Rules
1. ALWAYS query the database first before answering any question about grades, submissions, or assignments — never guess or assume data
2. When asked to grade an assignment, find ALL submissions for that assignment and grade each one
3. Never make up grades, scores, or student data
4. If a tool call fails or returns no data, inform the user clearly instead of guessing
5. After grading, always confirm how many submissions were graded and if any failed
6. If the user provides an assignment ID, use it directly — do not ask for it again
7. Always be concise and structured in your responses

## Tool Usage
- Use `get_data_from_db` for any data retrieval (grades, students, submissions, assignments)
- Use `assignment_id_based_homework_checker` to grade ALL submissions under an assignment
- Use `submission_number_based_homework_checker` to grade a SINGLE specific submission

## Response Format
- For reports: use clear sections with headers
- For grading results: list each submission with score and status
- For errors: clearly state what went wrong and what the user can do
"""

def ta_agent_main(prompt):
    messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content" : prompt}
    ]
    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages= messages,
            tools = tools)
        


        choice  = response.choices[0]

        if choice.finish_reason == "tool_calls":
            print("tool called .......")
            for tool_call in choice.message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)


                if name == "get_data_from_db":
                    res = get_data_from_db(args["query"])
                    messages.append(choice.message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(res)
                    })

                if name == "assignment_id_based_homework_checker":
                    res = assignment_id_based_homework_checker(args["aid"])
                    if res == True:
                        print("Done")
                    else:
                        print("Not done")
                    messages.append(choice.message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(res)
                    })

                if name == "submission_number_based_homework_checker":
                    res = assignment_id_based_homework_checker(args["sid"])
                    if res == True:
                        print("Done")
                    else:
                        print("Not done")
                    messages.append(choice.message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(res)
                    })

        elif choice.finish_reason == "stop":   
            return choice.message.content


  











if __name__ == "__main__":


    print(ta_agent_main("can u make a report for all the student in the DB?"))





















#     print(excecute_sql("What is the min and max marks a person has scored in any of the graded submission"))# def ta_agent_main(prompt):
