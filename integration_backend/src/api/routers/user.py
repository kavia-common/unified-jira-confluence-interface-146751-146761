from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List

from ..models.user import UserCreate, UserUpdate, UserResponse
from ..services.user import user_service
from ..auth import create_access_token, verify_token

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        
    Returns:
        UserResponse: Created user
    """
    return await user_service.create_user(user_data)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login and get access token
    
    Args:
        form_data: OAuth2 password request form
        
    Returns:
        dict: Access token response
    """
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "scopes": [user.role.value]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user profile
    
    Args:
        token: OAuth access token
        
    Returns:
        UserResponse: Current user profile
    """
    token_data = verify_token(token)
    return await user_service.get_user_by_username(token_data["sub"])

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    token: str = Depends(oauth2_scheme)
):
    """
    Update current user profile
    
    Args:
        update_data: User update data
        token: OAuth access token
        
    Returns:
        UserResponse: Updated user profile
    """
    token_data = verify_token(token)
    return await user_service.update_user(token_data["sub"], update_data)

@router.get("/", response_model=List[UserResponse])
async def list_users(token: str = Depends(oauth2_scheme)):
    """
    List all users (admin only)
    
    Args:
        token: OAuth access token
        
    Returns:
        List[UserResponse]: List of users
    """
    token_data = verify_token(token)
    if "admin" not in token_data.get("scopes", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return await user_service.list_users()
