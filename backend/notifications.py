"""Escalation SMTP notifications with persistent duplicate prevention."""
import logging
import os
import smtplib
from email.message import EmailMessage
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal, Notification

logger = logging.getLogger(__name__)

def notify_escalation(ticket, customer=None):
    """Send once per ticket/recipient; log failures without interrupting ticket creation."""
    recipient = os.getenv('SMTP_TO_EMAIL', '').strip()
    if not recipient:
        logger.warning('Escalation email skipped: SMTP_TO_EMAIL is missing')
        return False
    with SessionLocal() as db:
        existing = db.query(Notification).filter_by(ticket_id=ticket.id, recipient=recipient).filter(Notification.state.in_(['Sent', 'Sending'])).first()
        if existing:
            return existing.state == 'Sent'
        row = db.query(Notification).filter_by(ticket_id=ticket.id, recipient=recipient).first()
        if row is None:
            row = Notification(ticket_id=ticket.id, recipient=recipient, subject=f'[CRM ESCALATION] TKT-{ticket.id:04d}', state='Sending')
            db.add(row)
        else:
            row.state = 'Sending'
        db.commit()
        row_id = row.id
    try:
        host = os.getenv('SMTP_HOST', '').strip()
        user = os.getenv('SMTP_USER', '').strip()
        password = os.getenv('SMTP_PASSWORD', '').strip()
        sender = os.getenv('SMTP_FROM', user).strip()
        port = int(os.getenv('SMTP_PORT', '587'))
        if not all([host, user, password, sender]):
            raise ValueError('Missing SMTP_HOST, SMTP_USER, SMTP_PASSWORD, or SMTP_FROM')
        message = EmailMessage()
        message['From'] = sender
        message['To'] = recipient
        message['Subject'] = f'[CRM ESCALATION] TKT-{ticket.id:04d} | {ticket.urgency or "Unknown"} priority'
        message.set_content(f"""An AI CRM ticket requires human review.

Ticket: TKT-{ticket.id:04d}
Priority: {ticket.urgency}
Status: {ticket.status}
Category: {ticket.category}
Customer: {getattr(customer, 'name', '')}
Customer email: {getattr(customer, 'email', '')}
Reason: {ticket.escalation_reason or 'Human assistance requested'}

Complaint:
{ticket.complaint}

Review this ticket in the CRM Human Review page.
""")
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(message)
        state = 'Sent'
    except Exception:
        logger.exception('SMTP escalation notification failed for ticket %s', ticket.id)
        state = 'Failed'
    with SessionLocal() as db:
        row = db.get(Notification, row_id)
        if row:
            row.state = state
            db.commit()
    return state == 'Sent'
