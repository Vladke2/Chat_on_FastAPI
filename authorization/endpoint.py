from fastapi import Depends, HTTPException, status, FastAPI
from sqlalchemy.orm import Session
from .auth import get_password_hash, verify_password,  create_access_token,\
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .schemas import UserCreate
from models import database, User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import timedelta


app = FastAPI()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = database.Session()
    try:
        yield db
    finally:
        db.close()


@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> dict:
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"username": db_user.username}


@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return {"username": user.username, 'id': user.id}
