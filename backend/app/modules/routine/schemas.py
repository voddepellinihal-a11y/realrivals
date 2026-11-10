from pydantic import BaseModel, Field


class RoutineCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    time: str = Field(min_length=4, max_length=8)  # "HH:MM"
    frequency: str = Field(default="daily", max_length=32)
    notes: str = Field(default="", max_length=512)
    xp: int = Field(default=25, ge=0, le=10000)
    category: str = Field(default="health", max_length=64)
