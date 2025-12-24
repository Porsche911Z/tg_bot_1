from sqlalchemy.orm import Session
from app.database.models import User, Message


def get_or_create_user(db: Session, telegram_id: str, username: str | None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        return user

    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_message(db: Session, user: User, question: str, answer: str):
    msg = Message(user_id=user.id, question=question, answer=answer)
    db.add(msg)
    db.commit()