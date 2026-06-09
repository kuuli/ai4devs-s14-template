from pydantic import BaseModel, Field

TIPOS_VALIDOS: set[str] = {"Bug", "Task", "Story", "Question"}
PRIORIDADES_VALIDAS: set[str] = {"Blocker", "High", "Medium", "Low"}


class CreateTicketInput(BaseModel):
    resumen: str = Field(..., min_length=5, max_length=255)
    descripcion: str = Field(..., min_length=10)
    tipo: str = Field(default="Task", pattern="^(Bug|Task|Story|Question)$")
    prioridad: str = Field(default="Medium", pattern="^(Blocker|High|Medium|Low)$")


class TicketDraft(BaseModel):
    project_key: str
    resumen: str
    descripcion: str
    tipo: str = "Task"
    prioridad: str = "Medium"
    parent_key: str = "L1DR-53"  # epic — fixed, never overridable by the user
