from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response models read straight from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class EmployeeBrief(ORMModel):
    id: int
    full_name: str
    designation: str


class Message(BaseModel):
    detail: str
