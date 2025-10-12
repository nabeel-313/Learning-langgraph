from ai_travel_planner import langgraph_chatbot
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn

# Import our database and auth services
from src.database.databases import database  # ✅ Fixed import
from src.auth.authentication import AuthenticationService
from src.cache.session_manager import session_manager

app = FastAPI(title="Travel AI Assistant", debug=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Pydantic Models


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]


class AuthResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None
    user: Optional[UserResponse] = None


class ChangePasswordRequest(BaseModel):
    session_token: str
    current_password: str
    new_password: str


# Session Helper Functions
def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from request"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")

    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token

    return None


async def get_current_user_from_request(request: Request):
    """Get current user from request"""
    session_token = get_session_token(request)
    if not session_token:
        return None

    with database.get_session() as db:  # ✅ Fixed - using instance
        auth_service = AuthenticationService(db)
        return auth_service.get_current_user(session_token)


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    with database.get_session() as db:  # ✅ Fixed - using instance
        auth_service = AuthenticationService(db)

        result = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )

        if result["success"]:
            user_data_dict = {
                "email": user_data.email,
                "name": user_data.name
            }
            session_token = session_manager.create_session(
                result["user_id"],
                user_data_dict
            )

            if session_token:
                return AuthResponse(
                    success=True,
                    message="Registration successful",
                    session_token=session_token,
                    user=UserResponse(
                        id=result["user_id"],
                        email=user_data.email,
                        name=user_data.name
                    )
                )

        return AuthResponse(
            success=False,
            message=result.get("error", "Registration failed")
        )


@app.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    """Login user and create session"""
    with database.get_session() as db:  # ✅ Fixed - using instance
        auth_service = AuthenticationService(db)

        result = auth_service.login_user(
            email=credentials.email,
            password=credentials.password
        )

        if result["success"]:
            user = auth_service.get_current_user(result["session_token"])

            return AuthResponse(
                success=True,
                message="Login successful",
                session_token=result["session_token"],
                user=UserResponse(**user) if user else None
            )

        return AuthResponse(
            success=False,
            message=result.get("error", "Login failed")
        )


@app.post("/auth/logout")
async def logout(session_token: str):
    """Logout user by invalidating session"""
    success = session_manager.delete_session(session_token)
    return {
        "success": success,
        "message": "Logged out successfully" if success else "Logout failed"
    }


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(session_token: str):
    """Get current user details"""
    with database.get_session() as db:  # ✅ Fixed - using instance
        auth_service = AuthenticationService(db)
        user = auth_service.get_current_user(session_token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        return UserResponse(**user)


@app.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest):
    """Change user password"""
    with database.get_session() as db:  # ✅ Fixed - using instance
        auth_service = AuthenticationService(db)

        result = auth_service.change_password(
            session_token=request.session_token,
            current_password=request.current_password,
            new_password=request.new_password
        )

        return result


@app.post('/data')
async def get_data(request: Request):
    data = await request.json()
    text = data.get('data')
    user_input = text

    user = await get_current_user_from_request(request)
    user_id = user["id"] if user else None

    print(f"User input: {user_input} (User ID: {user_id})")

    out = langgraph_chatbot(user_input)

    print("---" * 100)
    print(out)
    print("---" * 100)

    response_message = out["output"] if isinstance(out, dict) and "output" in out else str(out)

    return JSONResponse({
        "response": True,
        "message": response_message,
        "user_authenticated": user_id is not None
    })

# Simple connection test
try:
    from src.cache.redis_client import redis_client
    if redis_client.is_connected():
        print("✅ Redis connected successfully")
    else:
        print("❌ Redis connection failed")
except Exception as e:
    print(f"❌ Redis connection error: {e}")

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
