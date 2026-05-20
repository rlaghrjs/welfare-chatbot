from pydantic import BaseModel, ConfigDict


class WelfarePolicyResponse(BaseModel):
    id: int
    inq_num: int | None = None

    intrs_thema_array: str | None = None
    jur_mnof_nm: str | None = None
    jur_org_nm: str | None = None
    life_array: str | None = None
    onap_psblt_yn: str | None = None
    rprs_ctadr: str | None = None
    serv_dgst: str | None = None
    serv_dtl_link: str | None = None
    serv_id: str
    serv_nm: str | None = None
    sprt_cyc_nm: str | None = None
    srv_pvsn_nm: str | None = None
    svcfrst_reg_ts: str | None = None
    trgter_indvdl_array: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FetchWelfareResponse(BaseModel):
    message: str
    saved_count: int
    skipped_count: int
