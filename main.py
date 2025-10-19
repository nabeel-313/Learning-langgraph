from ai_travel_planner import langgraph_chatbot
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
from src.database.databases import database
from src.auth.authentication import AuthenticationService
from src.cache.session_manager import session_manager
from src.loggers import Logger

logger = Logger(__name__).get_logger()

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


try:
    database.create_tables()
except Exception as e:
    print(f"Error creating tables: {e}")


# Session Helper Functions
def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from request"""
    # Check cookies first (for browser requests)
    cookies = request.cookies
    if "session_token" in cookies:
        token = cookies["session_token"]
        # print("Found session token in cookies...")
        return token

    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # print("Found session token in Authorization header...")
        return token

    # Check X-Session-Token header (for JavaScript)
    x_session_token = request.headers.get("X-Session-Token")
    if x_session_token:
        # print("Found session token in X-Session-Token header...")
        return x_session_token

    # Check query parameter (fallback)
    session_token = request.query_params.get("session_token")
    if session_token:
        # print("Found session token in query parameter...")
        return session_token

    # print("No session token found in request")
    return None


async def get_current_user_from_request(request: Request):
    """Get current user from request"""
    session_token = get_session_token(request)
    if not session_token:
        return None

    with database.get_session() as db:
        auth_service = AuthenticationService(db)
        user = auth_service.get_current_user(session_token)
        if user:
            logger.info(f"User found: {user['email']} (ID: {user['id']})")
        else:
            logger.error("No user found for session token")
        return user


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renders the main index page ONLY if user is logged in.
    """
    # print("Checking session for request to /")
    user = await get_current_user_from_request(request)
    if not user:
        logger.debug("No user found, redirecting to login")
        return RedirectResponse(url="/login")

    logger.info(f"User authenticated: {user['email']}, showing chat")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Renders the login page.
    """
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Renders the registration page.
    """
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    with database.get_session() as db:
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
                logger.info(f"Registration successful - Session created for {user_data_dict}")
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
    with database.get_session() as db:
        auth_service = AuthenticationService(db)

        result = auth_service.login_user(
            email=credentials.email,
            password=credentials.password
        )

        if result["success"]:
            user = auth_service.get_current_user(result["session_token"])
            logger.info(f"Login successful for user: {user}")

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
    with database.get_session() as db:
        auth_service = AuthenticationService(db)
        user = auth_service.get_current_user(session_token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        return UserResponse(**user)


@app.post('/data')
async def get_data(request: Request):
    """
    Handles POST requests to process user data - REQUIRES AUTHENTICATION
    """
    # Check if user is authenticated
    user = await get_current_user_from_request(request)
    if not user:
        return JSONResponse(
            {"error": "Authentication required"},
            status_code=401
        )

    data = await request.json()
    text = data.get('data')
    user_input = text
    # Pass user context to chatbot
    out = langgraph_chatbot(user_input)
    response_message = out["output"] if isinstance(out, dict) and "output" in out else str(out)
    logger.info(f"AI message: {response_message}")
    return JSONResponse({
        "response": True,
        "message": response_message,
        "user_authenticated": True,
        "user_name": user.get("name")
    })


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
