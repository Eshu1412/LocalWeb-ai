"""
LocalWeb AI — SQLAlchemy ORM Models
All database tables for the lead pipeline, events, calls, messages, and sites.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, JSON,
)
from sqlalchemy.orm import relationship

from db.database import Base


# ── Helpers ─────────────────────────────────────────────────
def utcnow():
    return datetime.now(timezone.utc)

def new_uuid():
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════
# 1. BUSINESS LEAD — Core pipeline entity
# ═══════════════════════════════════════════════════════════
class BusinessLead(Base):
    __tablename__ = "business_leads"

    id          = Column(String(36), primary_key=True, default=new_uuid)
    name        = Column(String(500), nullable=False, index=True)
    phone       = Column(String(20), index=True)         # E.164 format
    email       = Column(String(255))
    address     = Column(String(1000))
    category    = Column(String(100), index=True)         # restaurant, salon, etc.
    area        = Column(String(200), index=True)          # city / district
    place_id    = Column(String(255), unique=True)         # Google Places ID
    lat         = Column(Float)
    lng         = Column(Float)
    has_website = Column(Boolean, default=False)
    website_url = Column(String(1000))                     # Existing site URL (if any)

    # Pipeline state
    status      = Column(String(50), default="DISCOVERED", index=True)
    preview_url = Column(String(1000))                     # Sample site URL
    live_url    = Column(String(1000))                     # Production site URL
    domain      = Column(String(255))                      # Custom domain

    # Payment
    stripe_customer_id   = Column(String(255))
    stripe_subscription_id = Column(String(255))
    plan        = Column(String(50))                       # starter / business / premium
    paid_at     = Column(DateTime(timezone=True))

    # Metadata
    source      = Column(String(50), default="google_places")  # google_places / yelp / manual
    notes       = Column(Text)
    extra_data  = Column(JSON, default=dict)

    # DNC flag
    do_not_contact = Column(Boolean, default=False)

    # Timestamps
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    events      = relationship("PipelineEvent", back_populates="lead")
    calls       = relationship("CallLog", back_populates="lead")
    messages    = relationship("WhatsAppMessage", back_populates="lead")

    __table_args__ = (
        Index("ix_lead_status_area", "status", "area"),
        Index("ix_lead_category_area", "category", "area"),
    )


# ═══════════════════════════════════════════════════════════
# 2. PIPELINE EVENT — Audit trail for every agent action
# ═══════════════════════════════════════════════════════════
class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id        = Column(String(36), primary_key=True, default=new_uuid)
    lead_id   = Column(String(36), ForeignKey("business_leads.id"), nullable=False, index=True)
    agent     = Column(String(100), nullable=False, index=True)
    event     = Column(String(100), nullable=False)
    payload   = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    lead = relationship("BusinessLead", back_populates="events")


# ═══════════════════════════════════════════════════════════
# 3. CALL LOG — Twilio voice call records
# ═══════════════════════════════════════════════════════════
class CallLog(Base):
    __tablename__ = "call_logs"

    id             = Column(String(36), primary_key=True, default=new_uuid)
    lead_id        = Column(String(36), ForeignKey("business_leads.id"), nullable=False, index=True)
    call_sid       = Column(String(100), unique=True)       # Twilio Call SID
    from_number    = Column(String(20))
    to_number      = Column(String(20))
    status         = Column(String(50))                      # queued / ringing / answered / completed / failed
    duration       = Column(Integer, default=0)              # seconds
    recording_url  = Column(String(1000))
    transcript     = Column(Text)
    intent         = Column(String(50))                      # interested / not_interested / needs_info
    sentiment      = Column(String(50))                      # positive / neutral / negative
    script_used    = Column(Text)
    retry_count    = Column(Integer, default=0)
    error_message  = Column(Text)

    created_at     = Column(DateTime(timezone=True), default=utcnow)

    lead = relationship("BusinessLead", back_populates="calls")

    __table_args__ = (
        Index("ix_call_status_created", "status", "created_at"),
    )


# ═══════════════════════════════════════════════════════════
# 4. WHATSAPP MESSAGE — Message records
# ═══════════════════════════════════════════════════════════
class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id          = Column(String(36), primary_key=True, default=new_uuid)
    lead_id     = Column(String(36), ForeignKey("business_leads.id"), nullable=False, index=True)
    message_id  = Column(String(255), unique=True)          # Meta message ID
    direction   = Column(String(10), nullable=False)        # inbound / outbound
    phone       = Column(String(20))
    body        = Column(Text)
    message_type = Column(String(20), default="text")       # text / image / interactive / template
    button_id   = Column(String(50))                        # Button reply ID
    status      = Column(String(20), default="sent")        # sent / delivered / read / failed
    media_url   = Column(String(1000))

    created_at  = Column(DateTime(timezone=True), default=utcnow)

    lead = relationship("BusinessLead", back_populates="messages")


# ═══════════════════════════════════════════════════════════
# 5. DEPLOYED SITE — Production websites we manage
# ═══════════════════════════════════════════════════════════
class DeployedSite(Base):
    __tablename__ = "deployed_sites"

    id             = Column(String(36), primary_key=True, default=new_uuid)
    lead_id        = Column(String(36), ForeignKey("business_leads.id"), unique=True)
    domain         = Column(String(255), unique=True)
    vercel_project_id = Column(String(255))
    template_used  = Column(String(100))
    status         = Column(String(50), default="building")  # building / live / suspended / error
    lighthouse_perf = Column(Float)
    lighthouse_seo  = Column(Float)
    lighthouse_a11y = Column(Float)
    llm_qa_score   = Column(Integer)

    deployed_at    = Column(DateTime(timezone=True))
    last_checked   = Column(DateTime(timezone=True))
    created_at     = Column(DateTime(timezone=True), default=utcnow)
    updated_at     = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ═══════════════════════════════════════════════════════════
# 6. ADMIN USER — Dashboard access control
# ═══════════════════════════════════════════════════════════
class AdminUser(Base):
    __tablename__ = "admin_users"

    id           = Column(String(36), primary_key=True, default=new_uuid)
    email        = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role         = Column(String(50), default="viewer")  # super_admin / ops_manager / viewer
    is_active    = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    last_login   = Column(DateTime(timezone=True))

    created_at   = Column(DateTime(timezone=True), default=utcnow)
    updated_at   = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ═══════════════════════════════════════════════════════════
# 7. DO NOT CONTACT — Persisted DNC records (also in Redis)
# ═══════════════════════════════════════════════════════════
class DoNotContact(Base):
    __tablename__ = "do_not_contact"

    id      = Column(String(36), primary_key=True, default=new_uuid)
    phone   = Column(String(20), unique=True, nullable=False, index=True)
    reason  = Column(String(500))
    added_by = Column(String(100), default="system")
    created_at = Column(DateTime(timezone=True), default=utcnow)
