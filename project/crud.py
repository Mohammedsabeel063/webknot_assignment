from typing import List, Optional, TypeVar, Type, Any, Dict, Union
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy import func, desc, or_, and_
import models
import schemas

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=schemas.BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=schemas.BaseModel)

class CRUDBase:
    def __init__(self, model: Type[ModelType]):
        """
        Base class for CRUD operations.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single object by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
        desc_order: bool = False
    ) -> List[ModelType]:
        """Get multiple objects with optional filtering and pagination"""
        query = db.query(self.model)
        
        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            query = query.order_by(desc(column) if desc_order else column)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new object"""
        obj_in_data = obj_in.dict(exclude_unset=True)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing object"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: Any) -> ModelType:
        """Delete an object by ID"""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

# College CRUD operations
class CRUDCollege(CRUDBase):
    def get_by_domain(self, db: Session, domain: str) -> Optional[models.College]:
        return db.query(self.model).filter(
            func.lower(self.model.domain) == domain.lower()
        ).first()
    
    def search(
        self, 
        db: Session, 
        *, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.College]:
        search = f"%{query}%"
        return db.query(self.model).filter(
            or_(
                self.model.name.ilike(search),
                self.model.domain.ilike(search),
                self.model.address.ilike(search)
            )
        ).offset(skip).limit(limit).all()

# Student CRUD operations
class CRUDStudent(CRUDBase):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Student]:
        return db.query(self.model).filter(
            func.lower(self.model.email) == email.lower()
        ).first()
    
    def get_by_roll_no(
        self, 
        db: Session, 
        college_id: str, 
        roll_no: str
    ) -> Optional[models.Student]:
        return db.query(self.model).filter(
            self.model.college_id == college_id,
            func.lower(self.model.roll_no) == roll_no.lower()
        ).first()
    
    def search(
        self, 
        db: Session, 
        *, 
        college_id: str, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Student]:
        search = f"%{query}%"
        return db.query(self.model).filter(
            self.model.college_id == college_id,
            or_(
                self.model.name.ilike(search),
                self.model.email.ilike(search),
                self.model.roll_no.ilike(search),
                self.model.department.ilike(search)
            )
        ).offset(skip).limit(limit).all()

# Event CRUD operations
class CRUDEvent(CRUDBase):
    def get_upcoming(
        self, 
        db: Session, 
        *, 
        college_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Event]:
        return db.query(self.model).filter(
            self.model.college_id == college_id,
            self.model.start_time > datetime.utcnow()
        ).order_by(self.model.start_time).offset(skip).limit(limit).all()
    
    def get_ongoing(
        self, 
        db: Session, 
        *, 
        college_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Event]:
        now = datetime.utcnow()
        return db.query(self.model).filter(
            self.model.college_id == college_id,
            self.model.start_time <= now,
            self.model.end_time >= now
        ).order_by(self.model.start_time).offset(skip).limit(limit).all()
    
    def get_past(
        self, 
        db: Session, 
        *, 
        college_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Event]:
        return db.query(self.model).filter(
            self.model.college_id == college_id,
            self.model.end_time < datetime.utcnow()
        ).order_by(desc(self.model.end_time)).offset(skip).limit(limit).all()
    
    def search(
        self, 
        db: Session, 
        *, 
        college_id: str, 
        query: str, 
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Event]:
        search = f"%{query}%"
        filters = [
            self.model.college_id == college_id,
            or_(
                self.model.title.ilike(search),
                self.model.description.ilike(search),
                self.model.venue.ilike(search)
            )
        ]
        
        if event_type:
            filters.append(self.model.type == event_type)
        
        if start_date:
            filters.append(self.model.start_time >= start_date)
        
        if end_date:
            filters.append(self.model.end_time <= end_date)
        
        return db.query(self.model).filter(*filters).order_by(
            desc(self.model.start_time)
        ).offset(skip).limit(limit).all()
    
    def get_registrations(
        self, 
        db: Session, 
        event_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Registration]:
        return db.query(models.Registration).filter(
            models.Registration.event_id == event_id
        ).offset(skip).limit(limit).all()
    
    def get_attendees(
        self, 
        db: Session, 
        event_id: str, 
        present: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Attendance]:
        query = db.query(models.Attendance).filter(
            models.Attendance.event_id == event_id
        )
        
        if present is not None:
            query = query.filter(models.Attendance.present == present)
        
        return query.offset(skip).limit(limit).all()

# Registration CRUD operations
class CRUDRegistration(CRUDBase):
    def get_by_student_and_event(
        self, 
        db: Session, 
        student_id: str, 
        event_id: str
    ) -> Optional[models.Registration]:
        return db.query(self.model).filter(
            self.model.student_id == student_id,
            self.model.event_id == event_id
        ).first()
    
    def get_student_events(
        self, 
        db: Session, 
        student_id: str,
        upcoming: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[models.Event]:
        query = db.query(models.Event).join(models.Registration).filter(
            models.Registration.student_id == student_id
        )
        
        now = datetime.utcnow()
        if upcoming is not None:
            if upcoming:
                query = query.filter(models.Event.start_time > now)
            else:
                query = query.filter(models.Event.end_time < now)
        
        return query.order_by(models.Event.start_time).offset(skip).limit(limit).all()

# Attendance CRUD operations
class CRUDAttendance(CRUDBase):
    def get_by_student_and_event(
        self, 
        db: Session, 
        student_id: str, 
        event_id: str
    ) -> Optional[models.Attendance]:
        return db.query(self.model).filter(
            self.model.student_id == student_id,
            self.model.event_id == event_id
        ).first()
    
    def get_event_attendance_stats(
        self, 
        db: Session, 
        event_id: str
    ) -> Dict[str, int]:
        result = db.query(
            func.count(models.Attendance.id).label("total"),
            func.sum(
                case([(models.Attendance.present == True, 1)], else_=0)
            ).label("present"),
            func.sum(
                case([(models.Attendance.present == False, 1)], else_=0)
            ).label("absent")
        ).filter(
            models.Attendance.event_id == event_id
        ).first()
        
        return {
            "total": result[0] or 0,
            "present": result[1] or 0,
            "absent": result[2] or 0
        }

# Feedback CRUD operations
class CRUDFeedback(CRUDBase):
    def get_by_student_and_event(
        self, 
        db: Session, 
        student_id: str, 
        event_id: str
    ) -> Optional[models.Feedback]:
        return db.query(self.model).filter(
            self.model.student_id == student_id,
            self.model.event_id == event_id
        ).first()
    
    def get_event_feedback_stats(
        self, 
        db: Session, 
        event_id: str
    ) -> Dict[str, Any]:
        # Get average rating
        result = db.query(
            func.avg(models.Feedback.rating).label("avg_rating"),
            func.count(models.Feedback.id).label("total_responses")
        ).filter(
            models.Feedback.event_id == event_id
        ).first()
        
        # Get rating distribution
        distribution = db.query(
            models.Feedback.rating,
            func.count(models.Feedback.id).label("count")
        ).filter(
            models.Feedback.event_id == event_id
        ).group_by(models.Feedback.rating).all()
        
        return {
            "average_rating": float(result[0]) if result[0] else 0,
            "total_responses": result[1] or 0,
            "rating_distribution": {str(r.rating): r.count for r in distribution}
        }

# Initialize CRUD instances
college = CRUDCollege(models.College)
student = CRUDStudent(models.Student)
event = CRUDEvent(models.Event)
registration = CRUDRegistration(models.Registration)
attendance = CRUDAttendance(models.Attendance)
feedback = CRUDFeedback(models.Feedback)
