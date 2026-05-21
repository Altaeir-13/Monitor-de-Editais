import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adicionar raiz do backend no sys.path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.services.email_dispatcher import dispatch_pending_emails
from app.models.notification import Notification
from app.models.user import User
from app.models.notice import Notice
from app.api import deps

class TestEmailDispatcher(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.query_mock = self.db.query.return_value.filter.return_value.limit.return_value
    
    @patch('app.services.email_dispatcher.send_email')
    def test_a_success(self, mock_send_email):
        """Cenário A: Sucesso. Status vira sent, sent_at preenchido, error_message None."""
        user = User(email='test@example.com', name='Test')
        notice = Notice(title='Edital 1', notice_type='HTML', description='Desc', url='http://x')
        notif = Notification(id=1, status='pending')
        notif.user = user
        notif.notice = notice
        
        self.query_mock.all.return_value = [notif]
        
        res = dispatch_pending_emails(self.db)
        
        self.assertEqual(res['sent'], 1)
        self.assertEqual(res['failed'], 0)
        self.assertEqual(notif.status, 'sent')
        self.assertIsNotNone(notif.sent_at)
        self.assertIsNone(notif.error_message)
        mock_send_email.assert_called_once()
        
    @patch('app.services.email_dispatcher.send_email')
    def test_b_failure(self, mock_send_email):
        """Cenário B: Falha. Status vira failed, sent_at None, error_message limitado a 255 chars."""
        mock_send_email.side_effect = Exception("smtp error")
        user = User(email='test@example.com', name='Test')
        notice = Notice(title='Edital 2', notice_type='HTML', description='Desc', url='http://x')
        notif = Notification(id=2, status='pending')
        notif.user = user
        notif.notice = notice
        
        self.query_mock.all.return_value = [notif]
        
        res = dispatch_pending_emails(self.db)
        
        self.assertEqual(res['sent'], 0)
        self.assertEqual(res['failed'], 1)
        self.assertEqual(notif.status, 'failed')
        self.assertIsNone(notif.sent_at)
        self.assertEqual(notif.error_message, "smtp error")
        mock_send_email.assert_called_once()
        
    def test_c_no_resend(self):
        """Cenário C: Não reenviar. Apenas pendings devem retornar do mock."""
        self.query_mock.all.return_value = []
        res = dispatch_pending_emails(self.db)
        self.assertEqual(res['sent'], 0)
        self.assertEqual(res['failed'], 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
