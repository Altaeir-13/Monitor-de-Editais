from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.core.email import send_email
import logging
from datetime import datetime, timezone
import html

logger = logging.getLogger(__name__)

def dispatch_pending_emails(db: Session, limit: int = 50) -> dict:
    """
    Finds notifications with status 'pending' and sends an email to the user.
    Updates status to 'sent' or 'failed' (recording error_message).
    Returns a dict with statistics.
    """
    pending_notifications = (
        db.query(Notification)
        .filter(Notification.status == 'pending')
        .limit(limit)
        .all()
    )

    if not pending_notifications:
        return {"sent": 0, "failed": 0}

    sent_count = 0
    failed_count = 0

    for notif in pending_notifications:
        # User and Notice relationships should be accessible (lazy loaded or joined if configured)
        user = notif.user
        notice = notif.notice

        if not user or not notice:
            notif.status = 'failed'
            notif.error_message = "Missing user or notice relation"
            failed_count += 1
            continue

        safe_title = html.escape(notice.title or "")
        safe_type = html.escape(notice.notice_type or "")
        safe_desc = html.escape(notice.description or 'Sem descrição')
        safe_url = html.escape(notice.url or "")

        subject = f"Novo Edital Encontrado: {notice.title}"
        html_content = f"""
        <html>
            <body>
                <h2>Um novo edital que combina com seu alerta foi detectado!</h2>
                <p><strong>Título:</strong> {safe_title}</p>
                <p><strong>Tipo:</strong> {safe_type}</p>
                <p><strong>Descrição:</strong> {safe_desc}</p>
                <br>
                <p><a href="{safe_url}">Clique aqui para acessar o edital oficial</a></p>
                <hr>
                <p><small>Você recebeu este e-mail através do sistema Monitor de Editais.</small></p>
            </body>
        </html>
        """

        try:
            send_email(
                email_to=user.email,
                subject=subject,
                html_content=html_content
            )
            notif.status = 'sent'
            notif.sent_at = datetime.now(timezone.utc)
            notif.error_message = None
            sent_count += 1
        except Exception as e:
            notif.status = 'failed'
            # Record error string up to 255 chars
            notif.error_message = str(e)[:255]
            failed_count += 1

    db.commit()

    return {
        "sent": sent_count,
        "failed": failed_count
    }
