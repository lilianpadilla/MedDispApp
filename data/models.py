from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    Time,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from data.connection import Base


class Nurse(Base):
    __tablename__ = "nurse"

    nurse_id = Column("nurseid", String(8), primary_key=True)
    name = Column("nursename", String(50))


class Drug(Base):
    __tablename__ = "drug"

    drug_id = Column("drugid", String(8), primary_key=True)
    name = Column("drugname", String(50))


class Ingredient(Base):
    __tablename__ = "ingredient"

    ingredient_id = Column("ingredientid", String(8), primary_key=True)
    name = Column("ingredientname", String(50))


class Patient(Base):
    __tablename__ = "patient"

    patient_id = Column("patientid", String(8), primary_key=True)
    name = Column("patientname", String(50))
    gender = Column("patientgender", String(10))
    dob = Column("patientdob", Date)

    intake_events = relationship("DrugIntakeEvent", back_populates="patient")


class Contain(Base):
    __tablename__ = "contain"

    ingredient_id = Column("ingredientid", String(8), ForeignKey("ingredient.ingredientid"), primary_key=True)
    drug_id = Column("drugid", String(8), ForeignKey("drug.drugid"), primary_key=True)
    amount = Column("amount", Integer)


class DrugIntakeEvent(Base):
    __tablename__ = "drugintakeevent"

    die_number = Column("dienumber", String(10), primary_key=True)
    patient_id = Column("patientid", String(8), ForeignKey("patient.patientid"))
    die_date = Column("diedate", Date)
    die_time = Column("dietime", Time)
    nurse_id = Column("nurseid", String(8), ForeignKey("nurse.nurseid"))

    patient = relationship("Patient", back_populates="intake_events")


class Includes(Base):
    __tablename__ = "includes"

    drug_id = Column("drugid", String(8), ForeignKey("drug.drugid"), primary_key=True)
    die_number = Column("dienumber", String(10), ForeignKey("drugintakeevent.dienumber"), primary_key=True)
    quantity = Column("quantity", Integer)


class NotToTakeWith(Base):
    __tablename__ = "nottotakewith"

    drug_id_taking = Column("drugidtaking", String(8), ForeignKey("drug.drugid"), primary_key=True)
    drug_id_not_to_take_with = Column("drugidnottotakewith", String(8), ForeignKey("drug.drugid"), primary_key=True)


class V2Drug(Base):
    __tablename__ = "v2drug"

    drug_id = Column("drugid", String(8), primary_key=True)
    name = Column("drugname", String(50))
    restricted_time = Column("restrictedtime", Integer)  # in hours
