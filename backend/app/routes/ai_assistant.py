from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import get_current_user
from app.services.ai_assistant_service import answer_question
from app.models.user import User

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])


@router.post("/ask")
def ask(question: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return answer_question(db, user.company_id, question)
