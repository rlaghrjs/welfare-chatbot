from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SubscriptionConditions(StrictModel):
    # Between fields: AND; within each list: OR. Empty lists do not restrict.
    regions: list[str] = Field(default_factory=list, max_length=30)
    themes: list[str] = Field(default_factory=list, max_length=30)
    age: int | None = Field(default=None, ge=0, le=120)
    include_keywords: list[str] = Field(default_factory=list, max_length=20)
    exclude_keywords: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_terms(self):
        for field in ("regions", "themes", "include_keywords", "exclude_keywords"):
            terms = [term.strip() for term in getattr(self, field)]
            if any(not term or len(term) > 100 for term in terms):
                raise ValueError("조건 값은 1~100자여야 합니다.")
            setattr(self, field, list(dict.fromkeys(terms)))
        if set(self.include_keywords) & set(self.exclude_keywords):
            raise ValueError("같은 키워드를 포함/제외 조건에 동시에 지정할 수 없습니다.")
        return self


class SubscriptionRequest(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    profile_id: UUID | None = None
    conditions: SubscriptionConditions = Field(default_factory=SubscriptionConditions)
    event_types: list[Literal["new", "updated", "unavailable", "restored"]] = Field(default_factory=lambda: ["new", "updated"], min_length=1, max_length=4)
    unknown_condition_policy: Literal["include", "exclude"] = "include"
    enabled: bool = True

    @model_validator(mode="after")
    def require_condition(self):
        c = self.conditions
        if self.profile_id is None and not (c.regions or c.themes or c.age is not None or c.include_keywords or c.exclude_keywords):
            raise ValueError("프로필 또는 구독 조건을 하나 이상 지정해주세요.")
        return self


class ProfileRequest(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    birth_date: date | None = None
    region: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_birth_date(self):
        if self.birth_date and self.birth_date > date.today():
            raise ValueError("생년월일은 미래일 수 없습니다.")
        return self
