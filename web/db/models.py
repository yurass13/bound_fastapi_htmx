import enum
from datetime import datetime, time

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ProcessingFileStatus(enum.Enum):
    OK = "Ok"
    PROCESSING = "Processing"
    WAITING = "Waiting"
    CANCELED = "Canceled"
    REMOVED = "Removed"
    ERROR = "Error"


class ProcessingFile(Base):
    __tablename__ = "processing_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    size: Mapped[int] = mapped_column(nullable=True)
    status: Mapped[ProcessingFileStatus] = mapped_column(default=ProcessingFileStatus.WAITING)
    handling_time: Mapped[time] = mapped_column(nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())

    @property
    def status_text_style(self) -> str:
        if self.status == ProcessingFileStatus.OK:
            return "text-success"
        elif self.status == ProcessingFileStatus.PROCESSING:
            return "text-muted"
        elif self.status == ProcessingFileStatus.WAITING:
            return "text-primary"
        else:
            return "text-danger"

    @property
    def file_path(self) -> str:
        return f"./media/processing_files/{str(self.id)}"

    @property
    def get_absolute_url(self) -> str:
        return f"/processing_files/{self.id}/detail/"
