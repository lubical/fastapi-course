from typing import List, Optional
from fastapi import Response, status, HTTPException, APIRouter
from fastapi.params import Depends

from sqlalchemy.orm.session import Session
from sqlalchemy import func

from .. import models, schemas, oauth2, database


router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get("/", response_model=List[schemas.PostOut])
# @router.get("/")
def get_posts(db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user), 
        limit: int = 10, skip: int = 0, search: Optional[str]=""): 

    #posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
 
    # SELECT posts.*, count(votes.post_id) AS count_1 FROM posts LEFT OUTER JOIN votes ON posts.id = votes.post_id GROUP BY posts.id
    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(
            models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    
    return posts

@router.get("/{id}",  response_model=schemas.PostOut)
def get_post(id: int, db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user)):
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(
            models.Post.id).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"post with id: {id} does not exist")
    
    if post.Post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"not authorized to perform requested action")
    
    return post

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user)):
    new_post = models.Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)


@router.put("/{id}",  response_model=schemas.Post)
def update_post(id: int, updated_post:schemas.PostCreate, db: Session = Depends(database.get_db), 
        current_user=Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id) 
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"not authorized to perform requested action")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()
