from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import uuid

app = FastAPI(title="Python Code Runner API")

class CodeRequest(BaseModel):
    code: str
    lang: str
    timeout: int = 5  # Default timeout in seconds

class CodeResponse(BaseModel):
    output: str
    error: str = None
    execution_time: float = None
    

@app.post("/run", response_model=CodeResponse)
async def run_code(request: CodeRequest):
    # Create a unique ID for this execution
    execution_id = str(uuid.uuid4())
    
    # Create a temporary file with the code
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(request.code.encode())
    
    try:
        # Run the code in a separate process with timeout
        
        command = 'python'
        
        if request.lang == "javascript":
            command = "node"
        
        process = subprocess.run(
            [command, temp_file_path],
            capture_output=True,
            text=True,
            timeout=request.timeout
        )
        
        return CodeResponse(
            output=process.stdout,
            error=process.stderr,
            execution_time=process.returncode
        )
    
    except subprocess.TimeoutExpired:
        return CodeResponse(
            output="",
            error=f"Execution timed out after {request.timeout} seconds"
        )
    
    except Exception as e:
        return CodeResponse(
            output="",
            error=f"Error executing code: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.get("/")
async def root():
    return {"message": "Python Code Runner API"}