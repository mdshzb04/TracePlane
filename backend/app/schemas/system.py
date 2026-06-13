from pydantic import BaseModel, Field


class ReadinessCategory(BaseModel):
    id: str
    name: str
    score: int = Field(ge=0, le=100)
    status: str = Field(pattern=r"^(ready|partial|missing)$")
    detail: str
    missing_work: list[str] = Field(default_factory=list)


class ProductionReadinessResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    categories: list[ReadinessCategory]
    blockers: list[str] = Field(default_factory=list)
