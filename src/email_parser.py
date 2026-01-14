"""
Email Parser - Extracts data from Gmail messages
"""

import re
import base64
from email.header import decode_header
import html
from datetime import datetime

class EmailParser:
    """Parses Gmail API message objects"""
    
    @staticmethod
    def parse_email_message(message):
        """Parse a Gmail message into structured data"""
        try:
            headers = message.get('payload', {}).get('headers', [])
            
            # Extract components
            sender = EmailParser._extract_sender(headers)
            subject = EmailParser._extract_subject(headers)
            date = EmailParser._extract_date(headers)
            message_id = message.get('id', '')
            
            # Extract body
            body = EmailParser._extract_body(message.get('payload', {}))
            
            # Clean body text
            body = EmailParser._clean_body_text(body)
            
            return {
                'message_id': message_id,
                'sender': sender,
                'subject': subject,
                'date': date,
                'body': body
            }
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    @staticmethod
    def _extract_sender(headers):
        """Extract sender email from headers"""
        for header in headers:
            if header['name'].lower() == 'from':
                sender_text = header['value']
                email_match = re.search(r'<([^>]+)>', sender_text)
                if email_match:
                    return email_match.group(1)
                return sender_text
        return "Unknown Sender"
    
    @staticmethod
    def _extract_subject(headers):
        """Extract and decode email subject"""
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                try:
                    decoded_parts = decode_header(subject)
                    decoded_subject = ''
                    for part, encoding in decoded_parts:
                        if isinstance(part, bytes):
                            if encoding:
                                decoded_subject += part.decode(encoding)
                            else:
                                decoded_subject += part.decode('utf-8', errors='ignore')
                        else:
                            decoded_subject += str(part)
                    return decoded_subject.strip()
                except:
                    return subject.strip()
        return "No Subject"
    
    @staticmethod
    def _extract_date(headers):
        """Extract and format email date"""
        for header in headers:
            if header['name'].lower() == 'date':
                date_str = header['value']
                try:
                    # Try common date formats
                    date_formats = [
                        '%a, %d %b %Y %H:%M:%S',
                        '%d %b %Y %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            date_obj = datetime.strptime(date_str[:25], fmt)
                            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            continue
                    
                    # If parsing fails, return original (truncated)
                    return date_str[:50]
                except:
                    return date_str[:50]
        return "Unknown Date"
    
    @staticmethod
    def _extract_body(payload):
        """Extract plain text body from email payload"""
        body = ""
        
        # Check for multi-part email
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                # Look for plain text
                if mime_type == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        try:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break
                        except:
                            pass
                
                # Fallback to HTML
                elif mime_type == 'text/html' and not body:
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        try:
                            html_content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            body = EmailParser._html_to_text(html_content)
                        except:
                            pass
        
        # Check root body
        elif 'body' in payload and 'data' in payload['body']:
            body_data = payload['body'].get('data', '')
            if body_data:
                try:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                except:
                    pass
        
        return body
    
    @staticmethod
    def _clean_body_text(body):
        """Clean and truncate email body"""
        if not body:
            return "No body content"
        
        # Remove excessive whitespace
        body = ' '.join(body.split())
        
        # Unescape HTML
        body = html.unescape(body)
        
        # Remove common signatures
        signature_patterns = [
            r'--\s*\n.*$',
            r'Sent from my.*$',
            r'________________________________.*$',
            r'Best regards,.*$',
        ]
        
        for pattern in signature_patterns:
            body = re.sub(pattern, '', body, flags=re.MULTILINE | re.IGNORECASE)
        
        # Truncate if too long
        if len(body) > 2000:
            body = body[:1997] + "..."
        
        return body.strip()
    
    @staticmethod
    def _html_to_text(html_content):
        """Convert HTML to plain text"""
        # Remove script/style tags
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Replace tags with newlines
        html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<p[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        # Remove all other tags
        html_content = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Decode HTML entities
        html_content = html.unescape(html_content)
        
        # Clean whitespace
        html_content = ' '.join(html_content.split())
        
        return html_content
    
    @staticmethod
    def format_for_sheets(email_data):
        """Format email data for Google Sheets row"""
        if not email_data:
            return []
        
        return [
            email_data.get('sender', ''),
            email_data.get('subject', ''),
            email_data.get('date', ''),
            email_data.get('body', '')
        ]

    @staticmethod
    def filter_by_subject(email_data, keywords):
        """
        Filter emails by subject keywords - Bonus Feature
        
        Args:
            email_data: Parsed email dictionary
            keywords: List of keywords to filter by
            
        Returns:
            Boolean: True if email should be processed
        """
        if not keywords:
            return True
        
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        # Check if any keyword exists in subject or body
        for keyword in keywords:
            if keyword.lower() in subject or keyword.lower() in body:
                return True
        
        return False
    
    @staticmethod
    def extract_keywords(email_data, keywords):
        """
        Extract which keywords were found - Bonus Feature
        
        Returns:
            List of found keywords
        """
        found = []
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        for keyword in keywords:
            if keyword.lower() in subject or keyword.lower() in body:
                found.append(keyword)
        
        return found