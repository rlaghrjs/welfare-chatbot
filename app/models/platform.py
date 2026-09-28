"""Anonymous installations, policy catalog and condition subscriptions."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IdentityMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class CreatedMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppInstallation(IdentityMixin, CreatedMixin, Base):
    __tablename__ = "app_installations"
    token_hash: Mapped[str] = mapped_column(String(64))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Profile(IdentityMixin, CreatedMixin, Base):
    __tablename__ = "profiles"
    installation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_installations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    region: Mapped[str | None] = mapped_column(String(100))
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConditionSubscription(IdentityMixin, CreatedMixin, Base):
    __tablename__ = "condition_subscriptions"
    installation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_installations.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    conditions: Mapped[dict] = mapped_column(JSONB)
    event_types: Mapped[list] = mapped_column(JSONB)
    unknown_condition_policy: Mapped[str] = mapped_column(String(20), default="include")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (CheckConstraint("unknown_condition_policy IN ('include', 'exclude')", name="ck_subscription_unknown"),)


class SyncRun(IdentityMixin, Base):
    __tablename__ = "sync_runs"
    source: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="running")
    checkpoint: Mapped[dict] = mapped_column(JSONB, default=dict)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_sync_source_started", "source", "started_at"),)


class WelfarePolicy(IdentityMixin, Base):
    __tablename__ = "welfare_policies"
    source: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    search_attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    availability_status: Mapped[str] = mapped_column(String(30), default="available")
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_data: Mapped[dict] = mapped_column(JSONB)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    content_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_policy_source_external"),
        Index("ix_policy_availability", "availability_status"),
        Index("ix_policy_search_attributes", "search_attributes", postgresql_using="gin"),
    )


class WelfarePolicyVersion(IdentityMixin, Base):
    __tablename__ = "welfare_policy_versions"
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("welfare_policies.id", ondelete="RESTRICT"))
    sync_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sync_runs.id", ondelete="SET NULL"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[str] = mapped_column(String(30))
    snapshot: Mapped[dict] = mapped_column(JSONB)
    changes: Mapped[dict] = mapped_column(JSONB, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("policy_id", "version_no", name="uq_policy_version"),
        CheckConstraint("version_no > 0", name="ck_version_positive"),
    )


class PolicyEligibilityRule(IdentityMixin, Base):
    __tablename__ = "policy_eligibility_rules"
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("welfare_policy_versions.id", ondelete="CASCADE"), index=True)
    field: Mapped[str] = mapped_column(String(50))
    operator: Mapped[str] = mapped_column(String(30))
    value: Mapped[dict] = mapped_column(JSONB)
    evidence: Mapped[str] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")


class ChatSearchResult(IdentityMixin, Base):
    __tablename__ = "chat_search_results"
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"))
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("welfare_policy_versions.id", ondelete="RESTRICT"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("message_id", "policy_version_id", name="uq_chat_result_version"),
        CheckConstraint("rank > 0", name="ck_result_rank"),
    )


class Notification(IdentityMixin, CreatedMixin, Base):
    __tablename__ = "notifications"
    installation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_installations.id", ondelete="CASCADE"))
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("welfare_policy_versions.id", ondelete="RESTRICT"), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="app")
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    delivery_status: Mapped[str] = mapped_column(String(20), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("installation_id", "policy_version_id", "channel", name="uq_notification_delivery"),
        Index("ix_notification_unread", "installation_id", "read_at"),
        Index("ix_notification_retry", "delivery_status", "next_attempt_at"),
    )


class NotificationMatch(IdentityMixin, Base):
    __tablename__ = "notification_matches"
    notification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"))
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("condition_subscriptions.id", ondelete="SET NULL"), index=True)
    conditions_snapshot: Mapped[dict] = mapped_column(JSONB)
    match_reason: Mapped[dict] = mapped_column(JSONB)
    __table_args__ = (UniqueConstraint("notification_id", "subscription_id", name="uq_notification_match"),)
