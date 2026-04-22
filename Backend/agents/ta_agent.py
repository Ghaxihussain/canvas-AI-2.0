import sys
import os
import re
import base64
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from sqlalchemy import text, select, Update
from pydantic import BaseModel, Field

from Backend.services.aws import get_s3_object
from Backend.db.database import SessionLocal
from Backend.db.submissions import Submission
from Backend.db.assignments import Assignment
from Backend.db.classes import Class

class GradeResponse(BaseModel):
    grade: float = Field(description="the score of the student out of total grade")
    feedback: str = Field(description="detailed feedback for the student")


class TAAgent:

    SYSTEM_PROMPT = """You are a TA (Teaching Assistant) AI agent for a Canvas-like learning management system.
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

    def __init__(self, user_id):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.user_id = user_id


        with open("Backend/agents/ta_agent_tools.json") as f:
            self.tools = json.load(f)

        with open("Backend/db_structure.json") as f:
            self.structure = json.load(f)


    def build_content_block(self, data, content_type, label):
        blocks = [{"type": "text", "text": f"--- {label} ---"}]

        if content_type.startswith("text/"):
            blocks.append({"type": "text", "text": data.decode("utf-8")})

        elif content_type.startswith("image/"):
            b64 = base64.b64encode(data).decode("utf-8")
            blocks.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{b64}"}})

        elif content_type == "application/pdf":
            b64 = base64.b64encode(data).decode("utf-8")
            blocks.append({"type": "file", "file": {"filename": f"{label}.pdf", "file_data": f"data:application/pdf;base64,{b64}"}})

        return blocks

    def check_hw(self, assignment_key, submission_key, rubric_key=None, rubric_text=None, total_grade=100):
        bucket = os.getenv("AWS_BUCKET_NAME")
        rubric = []

        if rubric_key is None and rubric_text is None:
            rubric = [{"type": "text", "text": "--- RUBRIC ---\nCHECK THIS BASED ON YOUR KNOWLEDGE"}]

        if rubric_key:
            data, content_type = get_s3_object(bucket, rubric_key)
            rubric += self.build_content_block(data, content_type, "RUBRIC FILE")

        if rubric_text:
            rubric += [{"type": "text", "text": f"--- RUBRIC TEXT ---\n{rubric_text}"}]

        assignment_data, assignment_ct = get_s3_object(bucket, assignment_key)
        submission_data, submission_ct = get_s3_object(bucket, submission_key)

        content = [
            *rubric,
            *self.build_content_block(assignment_data, assignment_ct, "ASSIGNMENT"),
            *self.build_content_block(submission_data, submission_ct, "SUBMISSION"),
            {"type": "text", "text": f"Now grade the submission out of {total_grade} points."}
        ]

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a strict but fair homework grader. Total grade is out of {total_grade} points."},
                {"role": "user", "content": content}
            ],
            response_format=GradeResponse
        )
        return response.choices[0].message.parsed

    def assignment_id_based_homework_checker(self, aid):
        try:
            with SessionLocal() as db:
                assignment = db.execute(select(Assignment).where(Assignment.id == aid, (Assignment.created_by) == self.user_id)).scalar_one_or_none()
                if not assignment:
                    print(f"Assignment {aid} not found or the owner is wrong")
                    return False

                submissions = db.execute(select(Submission).where(Submission.assignment_id == aid)).scalars().all()
                print(f"Grading {len(submissions)} submissions...")

                for submission in submissions:
                    if not assignment.assignment_file_url and not assignment.text_content:
                        print(f"Skipping submission {submission.id} — no assignment content")
                        continue

                    res = self.check_hw(
                        submission_key=submission.file_url,
                        assignment_key=assignment.assignment_file_url,
                        rubric_text=assignment.rubric_text_content,
                        rubric_key=assignment.rubric_file_url,
                        total_grade=assignment.total_grade
                    )
                    Submission.grade_submission(
                        assignment_id=aid,
                        user_id=submission.user_id,
                        grade=res.grade,
                        feedback=f"AI Generated Feedback\n{res.feedback}",
                        db=db
                    )
            return True

        except Exception as e:
            print(f"Error grading assignment {aid}: {e}")
            return False



    def submission_number_based_homework_checker(self, sid):
        try:
            with SessionLocal() as db:
                submission = db.execute(select(Submission).where(str(Submission.id)== sid)).scalar_one_or_none()
                if not submission:
                    print(f"Submission {sid} not found")
                    return False

                assignment = db.execute(select(Assignment).where(Assignment.id == submission.assignment_id, (Assignment.created_by) == self.user_id)).scalar_one_or_none()
                if not assignment:
                    print(f"Assignment was not created by the {self.user_id}")
                    return False
                res = self.check_hw(
                    submission_key=submission.file_url,
                    assignment_key=assignment.assignment_file_url,
                    rubric_text=assignment.rubric_text_content,
                    rubric_key=assignment.rubric_file_url,
                    total_grade=assignment.total_grade
                )
                Submission.grade_submission(
                    assignment_id=submission.assignment_id,
                    user_id=submission.user_id,
                    grade=res.grade,
                    feedback=f"AI Generated Feedback\n{res.feedback}",
                    db=db
                )
            return True

        except Exception as e:
            print(f"Error grading submission {sid}: {e}")
            return False


    def generate_sql(self, query):
        prompt = f"""You are a SQL agent. Generate only valid SQL queries.
The database is PostgreSQL with this schema:
<schema>{self.structure}</schema>

Rules:
- Only return the SQL query, no explanation
- Use table aliases for joins
- Never use SELECT *
- You are not allowed to delete, update, or alter any data
- Only get the data from {self.user_id} 
Return ONLY the raw SQL query with no markdown or preamble."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": query}],
            temperature=0
        )
        return response.choices[0].message.content

    @staticmethod
    def extract_sql(raw):
        match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL)
        return match.group(1).strip() if match else raw.strip()

    @staticmethod
    def is_write_query(sql):
        return bool(re.search(r'\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE)\b', sql, re.IGNORECASE))
    
    
    def get_classes_info(self, class_code):
          
        with SessionLocal() as db:
            _class = Class.get_class_by_code(class_code = class_code, db = db)
            if not _class:
                print(class_code)
                print("No class found, hey")
                return None
            if str(_class.owner_id) != self.user_id:
                print("Auth error")
                return None
            return Class.get_students_by_code(class_code=class_code, db = db)
        
    

            
    def get_assignment_report(self, assignment_id):
        stats = {"total": 0, "max": 0, "min": 0, "avg": 0, "total_students": 0}

        with SessionLocal() as db:
            assignment = db.execute(
                select(Assignment).where(Assignment.id == assignment_id,Assignment.created_by == self.user_id)).scalar_one_or_none()

            if not assignment:
                print("assignment not found")
                return False

            stats["total"] = db.execute(text("SELECT total_grade FROM assignments WHERE id = :aid"),{"aid": assignment_id}).scalar()

            stats["max"] = db.execute(text("SELECT MAX(grade) FROM submissions WHERE assignment_id = :aid"),{"aid": assignment_id}).scalar()

            stats["min"] = db.execute(text("SELECT MIN(grade) FROM submissions WHERE assignment_id = :aid"),{"aid": assignment_id}).scalar()

            stats["avg"] = db.execute(text("SELECT AVG(grade) FROM submissions WHERE assignment_id = :aid"),{"aid": assignment_id}).scalar()

            stats["total_students"] = db.execute(text("SELECT COUNT(*) FROM submissions WHERE assignment_id = :aid"),{"aid": assignment_id}).scalar()

        return stats
    


    def get_class_assignment_based_report(self, class_code):
        with SessionLocal() as db:
            class_id = db.execute(select(Class.id).where(Class.owner_id == self.user_id,Class.class_code == class_code)).scalar_one_or_none()

            if not class_id:
                print("class not found")
                return False

            assignment_ids = db.execute(text("SELECT id FROM assignments WHERE class_id = :cid"),{"cid": class_id}).all()

            report = [{str(row.id): self.get_assignment_report(row.id)}for row in assignment_ids]

        return report


    

    def get_data_from_db(self, query):
        sql = self.extract_sql(self.generate_sql(query))

        if self.is_write_query(sql):
            return None

        try:
            with SessionLocal() as db:
                result = db.execute(text(sql))
                rows = result.fetchall()
                keys = result.keys()
            return {"result": [dict(zip(keys, row)) for row in rows], "sql": sql}
        except Exception as e:
            raise RuntimeError(f"DB query failed: {e}") from e


    def handle_tool(self, name, args):
        if name == "get_data_from_db":
            return str(self.get_data_from_db(args["query"]))

        elif name == "assignment_id_based_homework_checker":
            res = self.assignment_id_based_homework_checker(args["aid"])
            print("Done" if res else "Not done")
            return str(res)

        elif name == "submission_number_based_homework_checker":
            res = self.submission_number_based_homework_checker(args["sid"])
            print("Done" if res else "Not done")
            return str(res)
        elif name == "get_classes_info":
            res = self.get_classes_info(args["class_code"])
            print(args["class_code"], "this is the class code")
            print("Done" if res else "Not done")
            return str(res)
        elif name == "get_assignment_report":
            res = self.get_assignment_report(args["assignment_id"])
            print("Done" if res else "Not done")
            return str(res)
        elif name == "get_class_assignment_based_report":
            
            res = self.get_class_assignment_based_report(args["class_code"])
            print(res)
            print("Done" if res else "Not done")
            return str(res)
        return "Unknown tool"

    def run(self, prompt):
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                print("Tool called...")
                messages.append(choice.message) 

                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    result = self.handle_tool(name, args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

            elif choice.finish_reason == "stop":
                return choice.message.content




if __name__ == "__main__":
    agent = TAAgent(user_id="a1000000-0000-0000-0000-000000000001")
    for i in range(100):
        ui = input(":- ")
        if ui == "1":
            break
        print(agent.run(ui))
    

    pass
    


    # // {
    # //     "type": "function",
    # //     "function": {
    # //         "name": "get_data_from_db",
    # //         "description": "Gets the data from the database, the user must send the english sentance",
    # //         "parameters": {
    # //             "type": "object",
    # //             "properties": {
    # //                 "query": {"type": "string"}
    # //             },
    # //             "required": ["query"]
    # //         }
    # //     }
    # // },