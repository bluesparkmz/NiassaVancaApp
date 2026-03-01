from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemmas, models
from ..auth import get_current_user
from ..controllers import message as message_controller
from ..database import get_db

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=schemmas.MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    message_in: schemmas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not message_in.receiver_id and not message_in.group_id:
        raise HTTPException(status_code=400, detail="receiver_id ou group_id e obrigatorio")
    return message_controller.create_message(db, current_user.id, message_in)


@router.get("/conversation/{other_user_id}", response_model=list[schemmas.MessageOut])
def get_conversation(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return message_controller.get_conversation(db, current_user.id, other_user_id)


@router.put("/{message_id}", response_model=schemmas.MessageOut)
def update_message(
    message_id: int,
    payload: schemmas.MessageUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem nao encontrada")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o sender pode editar")
    return message_controller.update_message(db, message, payload.content)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem nao encontrada")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o sender pode apagar")
    message_controller.delete_message(db, message)
    return None


@router.get("/group/{group_id}", response_model=list[schemmas.MessageOut])
def get_group_messages(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Comentario: validar se o usuario pertence ao grupo.
    membership = (
        db.query(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id, models.GroupMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Usuario nao faz parte do grupo")
    return message_controller.get_group_messages(db, group_id)


@router.post("/groups", response_model=schemmas.GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    group_in: schemmas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = message_controller.create_group(db, current_user.id, group_in)
    # Comentario: adiciona o owner como membro.
    message_controller.add_group_member(
        db,
        group.id,
        schemmas.GroupMemberAdd(user_id=current_user.id, role="owner"),
    )
    return group


@router.put("/groups/{group_id}", response_model=schemmas.GroupOut)
def update_group(
    group_id: int,
    group_in: schemmas.GroupUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo nao encontrado")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o owner pode editar")
    return message_controller.update_group(db, group, group_in)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo nao encontrado")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o owner pode apagar")
    message_controller.delete_group(db, group)
    return None


@router.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: int,
    member_in: schemmas.GroupMemberAdd,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo nao encontrado")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o owner pode adicionar")
    return message_controller.add_group_member(db, group_id, member_in)


@router.delete("/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo nao encontrado")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o owner pode remover")
    message_controller.remove_group_member(db, group_id, user_id)
    return None
