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


if __name__ == "__main__":
    print(check_hw("assignment.pdf", "submission.pdf", "rubric.pdf", total_grade= 100))