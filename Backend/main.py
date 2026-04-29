from fastapi import FastAPI
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Backend.routes.accounts import acc_router
from Backend.routes.classes import class_router


app = FastAPI()
app.include_router(acc_router)
app.include_router(class_router)
@app.get("/")
def main():
    return {"code": 200}


