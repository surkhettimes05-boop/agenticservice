from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    prompt: str
    auto_approve: bool = True
    dry_run: bool | None = None


class TaskRunRead(BaseModel):
    id: int
    prompt: str
    status: str
    agent_id: str
    approval_requested: bool
    approval_approved: bool
    dry_run: bool
    output: str
    output_file: str
    created_at: datetime
    completed_at: datetime | None


class AgentRead(BaseModel):
    id: str
    name: str
    role: str
    department: str
    goal: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MVPWorkflowCreate(BaseModel):
    request: str


class MVPWorkflowRead(BaseModel):
    status: str
    delivery_dir: str
    completed_stages: list[str]


class LeadCandidate(BaseModel):
    company_name: str
    website: str
    industry: str
    employee_count: int
    signals: list[str] = []
    source: str


class LeadQualificationRequest(BaseModel):
    ideal_industries: list[str]
    min_employees: int = 1
    leads: list[LeadCandidate]
