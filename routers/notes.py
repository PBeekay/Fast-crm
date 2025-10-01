"""
Notes Router
Not yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

import models
import schemas
from dependencies import get_db, get_current_user

# Router oluştur
router = APIRouter(
    prefix="/api/customers",
    tags=["📝 Notes Management"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.post("/{customer_id}/notes", response_model=schemas.NoteOut)
def add_note(
    customer_id: int, 
    note_in: schemas.NoteCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Müşteriye not ekler"""
    logger.info(f"📝 Adding note to customer ID: {customer_id} (User: {current_user.email})")
    
    # Müşteriyi kontrol et
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found for note: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Not oluştur
    note = models.Note(
        customer_id=customer.id, 
        content=note_in.content, 
        created_by=current_user.id
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    logger.info(f"✅ Note added: ID {note.id} for customer {customer.name}")
    return note

@router.get("/{customer_id}/notes", response_model=List[schemas.NoteOut])
def list_notes(
    customer_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Müşterinin notlarını listeler"""
    logger.info(f"📋 Listing notes for customer ID: {customer_id} (User: {current_user.email})")
    
    # Müşteriyi kontrol et
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found for notes: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Notları getir
    notes = db.query(models.Note).filter(
        models.Note.customer_id == customer.id
    ).order_by(models.Note.created_at.desc()).all()
    
    logger.info(f"✅ Listed {len(notes)} notes for customer: {customer.name}")
    return notes

@router.get("/{customer_id}/notes/{note_id}", response_model=schemas.NoteOut)
def get_note(
    customer_id: int, 
    note_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Belirli bir notu getirir"""
    logger.info(f"🔍 Getting note ID: {note_id} for customer ID: {customer_id} (User: {current_user.email})")
    
    # Müşteriyi kontrol et
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Notu getir
    note = db.query(models.Note).filter(
        models.Note.id == note_id, 
        models.Note.customer_id == customer.id
    ).first()
    
    if not note:
        logger.warning(f"❌ Note not found: ID {note_id} for customer {customer.name}")
        raise HTTPException(status_code=404, detail="Note not found")
    
    logger.info(f"✅ Note retrieved: ID {note.id} for customer {customer.name}")
    return note

@router.put("/{customer_id}/notes/{note_id}", response_model=schemas.NoteOut)
def update_note(
    customer_id: int, 
    note_id: int, 
    note_update: schemas.NoteCreate,  # Reuse NoteCreate for updates
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Notu günceller"""
    logger.info(f"✏️ Updating note ID: {note_id} for customer ID: {customer_id} (User: {current_user.email})")
    
    # Müşteriyi kontrol et
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Notu getir
    note = db.query(models.Note).filter(
        models.Note.id == note_id, 
        models.Note.customer_id == customer.id
    ).first()
    
    if not note:
        logger.warning(f"❌ Note not found: ID {note_id} for customer {customer.name}")
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Notu güncelle
    note.content = note_update.content
    db.commit()
    db.refresh(note)
    
    logger.info(f"✅ Note updated: ID {note.id} for customer {customer.name}")
    return note

@router.delete("/{customer_id}/notes/{note_id}", status_code=204)
def delete_note(
    customer_id: int, 
    note_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Müşteri notunu siler"""
    logger.info(f"🗑️ Deleting note ID: {note_id} for customer ID: {customer_id} (User: {current_user.email})")
    
    # Müşteriyi kontrol et
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found for note deletion: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Notu getir
    note = db.query(models.Note).filter(
        models.Note.id == note_id, 
        models.Note.customer_id == customer.id
    ).first()
    
    if not note:
        logger.warning(f"❌ Note not found: ID {note_id} for customer {customer.name}")
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Notu sil
    db.delete(note)
    db.commit()
    
    logger.info(f"✅ Note deleted: ID {note_id} for customer {customer.name}")
    return
