"""
Google Calendar API Integration
Creates calendar events from natural language voice commands
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime, timedelta
import re

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        # Check if token exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

    def create_event(self, summary: str, start_time: datetime, duration_minutes: int = 60, attendees: list = None):
        """Create a calendar event"""
        service = build('calendar', 'v3', credentials=self.creds)

        end_time = start_time + timedelta(minutes=duration_minutes)

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',  # TODO: Make configurable
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        event_result = service.events().insert(calendarId='primary', body=event).execute()
        return event_result.get('htmlLink')


def parse_calendar_command(message: str) -> dict:
    """Extract calendar details from natural language"""
    # Simple regex-based parsing for demo
    # Production would use NLP (spaCy, etc.)

    # Extract time: "tomorrow at 3pm", "today at 2pm"
    time_match = re.search(r'(tomorrow|today)\s+at\s+(\d+)(:\d+)?\s*(pm|am)?', message.lower())

    if time_match:
        day = time_match.group(1)
        hour = int(time_match.group(2))
        minutes = int(time_match.group(3)[1:]) if time_match.group(3) else 0
        period = time_match.group(4) or 'pm'

        # Convert to 24-hour format
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        # Calculate datetime
        start_time = datetime.now()
        if day == 'tomorrow':
            start_time += timedelta(days=1)
        start_time = start_time.replace(hour=hour, minute=minutes, second=0, microsecond=0)
    else:
        # Default: tomorrow at 10am
        start_time = datetime.now() + timedelta(days=1)
        start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)

    # Extract meeting title
    # Everything before "tomorrow/today" or "at"
    title_match = re.match(r'schedule\s+(?:a\s+)?(.+?)(?:\s+tomorrow|\s+today|\s+at)', message.lower())
    title = title_match.group(1) if title_match else "Meeting"

    return {
        "title": title.title(),
        "start_time": start_time,
        "duration": 60
    }


# Singleton instance
_calendar_client = None


def get_calendar_client():
    """Get or create calendar client singleton"""
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
    return _calendar_client
