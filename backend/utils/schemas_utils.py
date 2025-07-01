from pydantic import BaseModel, EmailStr, constr
from typing import Literal


class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    confirm_password: str
    role: Literal["Client", "Developer"]
    source: Literal["MarketingAPI", "User Activity", "PlatformMonitor", "AWS"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PreferenceUpdate(BaseModel):
    viewName: str
    preferredView: str
    enabled: bool


class OAuthCompleteRequest(BaseModel):
    email: EmailStr
    role: str
    source: str


class CredentialRequest(BaseModel):
    ApiKey: str
    SecretKey: str
