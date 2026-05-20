from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WelfarePolicy(Base):
    __tablename__ = "welfare_policy"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    inq_num: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    intrs_thema_array: Mapped[str | None] = mapped_column(Text, nullable=True)
    jur_mnof_nm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jur_org_nm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    life_array: Mapped[str | None] = mapped_column(Text, nullable=True)
    onap_psblt_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rprs_ctadr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serv_dgst: Mapped[str | None] = mapped_column(Text, nullable=True)
    serv_dtl_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    serv_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    serv_nm: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sprt_cyc_nm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    srv_pvsn_nm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    svcfrst_reg_ts: Mapped[str | None] = mapped_column(String(255), nullable=True)

    trgter_indvdl_array: Mapped[str | None] = mapped_column(Text, nullable=True)
