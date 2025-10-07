"""
Customers Router
Müşteri yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

import models
import schemas
from dependencies import get_db, get_current_user, get_premium_user, get_active_user

# Router oluştur
router = APIRouter(
    prefix="/api/customers",
    tags=["👥 Customer Management"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger("fastcrm")

@router.post("/", response_model=schemas.CustomerOut)
def create_customer(
    customer_in: schemas.CustomerCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_premium_user)  # Premium kullanıcı gerekli
):
    """Yeni müşteri oluşturur (Premium kullanıcı gerekli)"""
    try:
        logger.info(f"👤 Premium user {current_user.email} creating customer: {customer_in.name}")
        logger.info(f"📊 Customer data received: name={customer_in.name}, email={customer_in.email}, phone={customer_in.phone}, company={customer_in.company}, status={customer_in.status}")
        
        customer = models.Customer(
            name=customer_in.name,
            email=customer_in.email,
            phone=customer_in.phone,
            company=customer_in.company,
            status=customer_in.status,
            owner_id=current_user.id
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        logger.info(f"✅ Customer created: {customer.name} (ID: {customer.id})")
        return customer
    except Exception as e:
        logger.error(f"❌ Error creating customer: {str(e)}")
        logger.error(f"❌ Customer data that caused error: {customer_in.dict()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create customer: {str(e)}"
        )

@router.get("/", response_model=List[schemas.CustomerOut])
def list_customers(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Kullanıcının müşterilerini listeler (sayfalama ve arama ile)"""
    query = db.query(models.Customer).filter(
        models.Customer.owner_id == current_user.id
    )
    
    # Arama filtresi ekle
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            models.Customer.name.ilike(search_term) |
            models.Customer.email.ilike(search_term) |
            models.Customer.company.ilike(search_term) |
            models.Customer.phone.ilike(search_term)
        )
        logger.info(f"🔍 Searching customers with term: '{search}' (User: {current_user.email})")
    
    customers = query.offset(skip).limit(limit).all()
    logger.info(f"📋 Listed {len(customers)} customers for user: {current_user.email}")
    return customers

@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(
    customer_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Belirli bir müşteriyi getirir"""
    logger.info(f"🔍 Getting customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    logger.info(f"✅ Customer retrieved: {customer.name} (ID: {customer.id})")
    return customer

@router.put("/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(
    customer_id: int, 
    customer_update: schemas.CustomerUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Müşteri bilgilerini günceller"""
    logger.info(f"✏️ Updating customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Sadece sağlanan alanları güncelle
    update_data = customer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    
    logger.info(f"✅ Customer updated: {customer.name} (ID: {customer.id})")
    return customer

@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Müşteriyi siler"""
    logger.info(f"🗑️ Deleting customer ID: {customer_id} (User: {current_user.email})")
    
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id, 
        models.Customer.owner_id == current_user.id
    ).first()
    
    if not customer:
        logger.warning(f"❌ Customer not found for deletion: ID {customer_id} (User: {current_user.email})")
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer_name = customer.name
    db.delete(customer)
    db.commit()
    
    logger.info(f"✅ Customer deleted: {customer_name} (ID: {customer_id})")
    return
