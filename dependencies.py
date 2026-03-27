from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .auth import decode_access_token
from .database import SessionLocal
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldn't validate credentials",
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get('sub')
        if user_id is None:
            raise credentials_error
        user_id = int(user_id)
    except Exception as exc:
        raise credentials_error from exc
    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user
