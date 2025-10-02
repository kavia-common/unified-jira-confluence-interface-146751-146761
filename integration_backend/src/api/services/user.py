from typing import List, Optional
from fastapi import HTTPException, status
from passlib.context import CryptContext
from ..models.user import UserCreate, UserUpdate, UserResponse

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Service class for handling user operations"""
    
    def __init__(self):
        # TODO: Replace with actual database
        self._users = {}
        self._next_id = 1

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    # PUBLIC_INTERFACE
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If username already exists
        """
        if user_data.username in self._users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Hash password and create user
        hashed_password = self._hash_password(user_data.password)
        user_dict = {
            "id": self._next_id,
            "username": user_data.username,
            "hashed_password": hashed_password,
            **user_data.dict(exclude={"password"})
        }
        
        self._users[user_data.username] = user_dict
        self._next_id += 1
        
        return UserResponse(**user_dict)

    # PUBLIC_INTERFACE
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[UserResponse]:
        """
        Authenticate a user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authenticated user or None
        """
        user = self._users.get(username)
        if not user:
            return None
        
        if not self._verify_password(password, user["hashed_password"]):
            return None
        
        return UserResponse(**user)

    # PUBLIC_INTERFACE
    async def get_user_by_username(self, username: str) -> UserResponse:
        """
        Get a user by username
        
        Args:
            username: Username
            
        Returns:
            User
            
        Raises:
            HTTPException: If user not found
        """
        user = self._users.get(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user)

    # PUBLIC_INTERFACE
    async def update_user(
        self,
        username: str,
        update_data: UserUpdate
    ) -> UserResponse:
        """
        Update a user
        
        Args:
            username: Username
            update_data: User update data
            
        Returns:
            Updated user
            
        Raises:
            HTTPException: If user not found
        """
        user = self._users.get(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_dict = update_data.dict(exclude_unset=True)
        if "password" in update_dict:
            update_dict["hashed_password"] = self._hash_password(update_dict.pop("password"))
        
        user.update(update_dict)
        return UserResponse(**user)

    # PUBLIC_INTERFACE
    async def list_users(self) -> List[UserResponse]:
        """
        List all users
        
        Returns:
            List of users
        """
        return [UserResponse(**user) for user in self._users.values()]

# Create global service instance
user_service = UserService()
