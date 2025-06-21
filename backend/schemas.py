from pydantic import BaseModel, EmailStr, constr
from typing import Literal


class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    confirm_password: str
    role: Literal["Client", "Developer"]
    source: Literal["MarketingAPI", "User Activity", "PlatformMonitor", "AWS"]
