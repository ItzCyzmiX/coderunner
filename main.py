from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
import subprocess
import tempfile
import os
import uuid

app = FastAPI(title="Python Code Runner API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class CodeRequest(BaseModel):
    code: str
    lang: str
    timeout: int = 5  # Default timeout in seconds

class CodeResponse(BaseModel):
    output: str
    error: str = None
    execution_time: float = None
    
def verify_token(token: str = Security(oauth2_scheme)):
    if token != os.environ.get('API_AUTH_KEY'):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@app.post("/run", response_model=CodeResponse)
async def run_code(request: CodeRequest, token: str = Depends(verify_token)):
    # Create a unique ID for this execution
    execution_id = str(uuid.uuid4())
    temp_file_path = ""
    extenstion = ".py"
    if request.lang == "javascript":
        extenstion = ".js"
    
    # Create a temporary file with the code
    with tempfile.NamedTemporaryFile(suffix=extenstion, delete=False) as temp_file:
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
    return {"langs": ["python", "javascript"]}