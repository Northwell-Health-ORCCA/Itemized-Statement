import enum  
import uuid  
from datetime import datetime, timezone

from sqlalchemy import (  
    Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint  
)  
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def now() -> datetime:  
    """Naive local time. Matches the YYYYMMDD_HHMMSS run_id format, so a run  
    named 20261116_091500 has start_time 09:15:00 — not 14:15 UTC."""  
    return datetime.now()


def new_uuid() -> str:  
    return str(uuid.uuid4())


# ---------- Enums ----------

class RunStatus(str, enum.Enum):  
    LOADED = "loaded"  
    IN_PROCESS = "in process"  
    COMPLETED = "completed"  
    FAILED = "failed"


class ItemStatus(str, enum.Enum):
    STAGED = "staged"
    SUCCESS = "success"  
    FAILED = "failed"


class ExceptionType(str, enum.Enum):  
    BUSINESS = "business exception"  
    APPLICATION = "application exception"
    PYTHON = "python exception"


# ---------- Tables ----------

class Run(Base):  
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)  
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  
    status: Mapped[RunStatus] = mapped_column(  
        Enum(RunStatus, native_enum=False, length=20),  
        nullable=False,  
        default=RunStatus.LOADED,  
    )  
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    failure_reason: Mapped[str | None] = mapped_column(Text)

    total_records: Mapped[int] = mapped_column(Integer, default=0)  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    inputs: Mapped[list["Input"]] = relationship(back_populates="run")  
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="run")

    def __repr__(self) -> str:  
        return f"<Run {self.run_id} {self.file_name} {self.status.value}>"


class Input(Base):  
    """Raw, unmodified rows from the CSV. Append-only audit of what came in."""  
    __tablename__ = "inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  
    run_id: Mapped[str] = mapped_column(  
        String(36), ForeignKey("runs.run_id"), nullable=False, index=True  
    )  
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  
    group_number: Mapped[str | None] = mapped_column(String(50))  
    row_number: Mapped[int | None] = mapped_column(Integer)  # line in the CSV  
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    run: Mapped["Run"] = relationship(back_populates="inputs")


class Output(Base):  
    """One row per invoice, ever. Holds the MOST RECENT attempt's result."""  
    __tablename__ = "outputs"

    invoice_number: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Provenance — set once, never updated  
    first_file_name: Mapped[str] = mapped_column(String(255), nullable=False)  
    first_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.run_id"))  
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    # Most recent attempt — overwritten each time  
    status: Mapped[ItemStatus | None] = mapped_column(  
        Enum(ItemStatus, native_enum=False, length=20)  
    )  
    exception_type: Mapped[ExceptionType | None] = mapped_column(  
        Enum(ExceptionType, native_enum=False, length=20)  
    )  
    exception_reason: Mapped[str | None] = mapped_column(Text)  
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    run_id: Mapped[str | None] = mapped_column(  
        String(36), ForeignKey("runs.run_id"), index=True  
    )  
    group_number: Mapped[str | None] = mapped_column(String(50))

    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  
    updated_at: Mapped[datetime] = mapped_column(  
        DateTime(timezone=True), default=now, onupdate=now  
    )

    attempts: Mapped[list["Attempt"]] = relationship(  
        back_populates="output", order_by="Attempt.attempt_number"  
    )

    __table_args__ = (  
        Index("ix_outputs_status_run", "status", "run_id"),  
    )


class Attempt(Base):  
    """Immutable log — one row per processing attempt per invoice."""  
    __tablename__ = "attempts"

    attempt_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  
    invoice_number: Mapped[str] = mapped_column(  
        String(50), ForeignKey("outputs.invoice_number"), nullable=False, index=True  
    )  
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)  
    run_id: Mapped[str] = mapped_column(  
        String(36), ForeignKey("runs.run_id"), nullable=False, index=True  
    )  
    group_number: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[ItemStatus] = mapped_column(  
        Enum(ItemStatus, native_enum=False, length=20), nullable=False  
    )  
    exception_type: Mapped[ExceptionType | None] = mapped_column(  
        Enum(ExceptionType, native_enum=False, length=20)  
    )  
    exception_reason: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    output: Mapped["Output"] = relationship(back_populates="attempts")  
    run: Mapped["Run"] = relationship(back_populates="attempts")

    __table_args__ = (  
        UniqueConstraint("invoice_number", "attempt_number", name="uq_attempt_seq"),  
    )  