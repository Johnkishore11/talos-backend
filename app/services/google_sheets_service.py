"""
Google Sheets service for syncing registrations to live tracking sheet.
Appends event and workshop registration data to organized Google Sheets.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.config import settings

class GoogleSheetsService:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self):
        self.service = None
        self.spreadsheet_id = settings.GOOGLE_SHEETS_ID
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service with service account credentials."""
        try:
            if not settings.GOOGLE_SERVICE_ACCOUNT_KEY:
                print("❌ WARNING: GOOGLE_SERVICE_ACCOUNT_KEY not set. Google Sheets sync disabled.")
                return
            
            if not settings.GOOGLE_SHEETS_ID:
                print("❌ WARNING: GOOGLE_SHEETS_ID not set. Google Sheets sync disabled.")
                return
            
            # Parse service account JSON
            if isinstance(settings.GOOGLE_SERVICE_ACCOUNT_KEY, str):
                cred_dict = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY)
            else:
                cred_dict = settings.GOOGLE_SERVICE_ACCOUNT_KEY
            
            print(f"📋 Google Sheets ID: {settings.GOOGLE_SHEETS_ID[:50]}...")
            print(f"📋 Service Account Email: {cred_dict.get('client_email', 'N/A')}")
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                cred_dict,
                scopes=self.SCOPES
            )
            
            # Build service
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Google Sheets service initialized successfully")
            
        except Exception as e:
            print(f"❌ ERROR initializing Google Sheets service: {str(e)}")
            import traceback
            traceback.print_exc()
            self.service = None
    
    def _ensure_sheet_exists(self, sheet_name: str, headers: List[str]) -> bool:
        """
        Ensure a sheet with the given name exists, create if it doesn't.
        Add headers if the sheet is newly created or empty.
        
        Args:
            sheet_name: Name of the sheet to check/create
            headers: List of column headers
            
        Returns:
            bool: True if sheet exists or was created successfully
        """
        try:
            if not self.service or not self.spreadsheet_id:
                return False
            
            # Get existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_exists = any(sheet['properties']['title'] == sheet_name for sheet in sheets)
            
            if not sheet_exists:
                # Create new sheet
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': 26
                                }
                            }
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                
                print(f"✓ Created new sheet: {sheet_name}")
                
                # Add headers
                header_body = {'values': [headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1',
                    valueInputOption='USER_ENTERED',
                    body=header_body
                ).execute()
                
                # Format header row (bold)
                format_request = {
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': self._get_sheet_id(sheet_name),
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'textFormat': {'bold': True},
                                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                                }
                            },
                            'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=format_request
                ).execute()
            
            return True
            
        except Exception as e:
            print(f"ERROR ensuring sheet exists '{sheet_name}': {str(e)}")
            return False
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """Get the sheet ID for a given sheet name."""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return 0
        except:
            return 0

    def append_event_registration(self, event_data: Dict[str, Any], leader_data: Dict[str, Any], members: List[Dict[str, Any]]) -> bool:
        """
        Append event registration row to event-specific sheet.
        Each event gets its own sheet named after the event.
        
        Args:
            event_data: {event_id, event_name, registration_id, registered_at, status}
            leader_data: {college_name, name, email, phone, year}
            members: List of {name, email, phone}
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                print("Google Sheets service not initialized")
                return False
            
            # Create sheet name from event name
            event_name = event_data.get('event_name', 'Unknown Event')
            sheet_name = f"Event - {event_name}"
            
            # Define headers for event registration
            headers = [
                'College Name', 'Event ID', 'Team Leader Email', 'Team Leader Name',
                'Team Leader Phone', 'Team Leader Year',
                'Member 1 Name', 'Member 1 Email', 'Member 1 Phone',
                'Member 2 Name', 'Member 2 Email', 'Member 2 Phone',
                'Member 3 Name', 'Member 3 Email', 'Member 3 Phone',
                'Referral ID', 'Registered At', 'Registration ID', 'Status', 'Team Name'
            ]
            
            # Ensure sheet exists
            if not self._ensure_sheet_exists(sheet_name, headers):
                print(f"Failed to create/access sheet: {sheet_name}")
                return False
            
            # Prepare row data
            row = [
                leader_data.get('college_name', ''),
                event_data.get('event_id', ''),
                leader_data.get('email', ''),
                leader_data.get('name', ''),
                leader_data.get('phone', ''),
                leader_data.get('year', ''),
            ]
            
            # Add member data (up to 3 members)
            for i in range(3):
                if i < len(members):
                    member = members[i]
                    row.extend([
                        member.get('name', ''),
                        member.get('email', ''),
                        member.get('phone', '')
                    ])
                else:
                    row.extend(['', '', ''])  # Empty slots for missing members
            
            # Add metadata
            row.extend([
                event_data.get('referral_id', ''),
                event_data.get('registered_at', ''),
                event_data.get('registration_id', ''),
                event_data.get('status', 'confirmed'),
                event_data.get('team_name', '')
            ])
            
            # Append to sheet
            body = {
                'values': [row]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A:T',  # Range covering all columns
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Event registration synced to '{sheet_name}': {event_data.get('registration_id')}")
            return True
            
        except Exception as e:
            print(f"ERROR appending event registration to Google Sheets: {str(e)}")
            return False
    
    def append_workshop_registration(self, workshop_data: Dict[str, Any], participant_data: Dict[str, Any]) -> bool:
        """
        Append workshop registration row to workshop-specific sheet.
        Each workshop gets its own sheet named after the workshop.
        
        Args:
            workshop_data: {workshop_id, workshop_name, registration_id, registered_at, status}
            participant_data: {college_name, name, email, phone, year, payment_id, payment_status, amount}
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                print("Google Sheets service not initialized")
                return False
            
            # Create sheet name from workshop name
            workshop_name = workshop_data.get('workshop_name', 'Unknown Workshop')
            sheet_name = f"Workshop - {workshop_name}"
            
            # Define headers for workshop registration
            headers = [
                'College Name', 'Workshop ID', 'Participant Name', 'Email',
                'Phone', 'Year', 'Payment ID', 'Amount', 'Payment Status',
                'Registered At', 'Registration ID', 'Status'
            ]
            
            # Ensure sheet exists
            if not self._ensure_sheet_exists(sheet_name, headers):
                print(f"Failed to create/access sheet: {sheet_name}")
                return False
            
            # Prepare row data
            row = [
                participant_data.get('college_name', ''),
                workshop_data.get('workshop_id', ''),
                participant_data.get('name', ''),
                participant_data.get('email', ''),
                participant_data.get('phone', ''),
                participant_data.get('year', ''),
                participant_data.get('payment_id', ''),
                participant_data.get('amount', ''),
                participant_data.get('payment_status', 'completed'),
                workshop_data.get('registered_at', ''),
                workshop_data.get('registration_id', ''),
                workshop_data.get('status', 'confirmed')
            ]
            
            # Append to sheet
            body = {
                'values': [row]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A:L',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Workshop registration synced to '{sheet_name}': {workshop_data.get('registration_id')}")
            return True
            
        except Exception as e:
            print(f"ERROR appending workshop registration to Google Sheets: {str(e)}")
            return False
    
    def update_stats_dashboard(self, stats_data: Dict[str, Any]) -> bool:
        """
        Update stats dashboard with live counts.
        
        Args:
            stats_data: {total_events, total_workshops, by_event: {...}, by_college: {...}}
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service or not self.spreadsheet_id:
                print("Google Sheets service not initialized")
                return False
            
            # Prepare stats rows
            rows = [
                ['LIVE REGISTRATION STATS'],
                ['Updated at:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                [],
                ['EVENTS'],
                ['Event Name', 'Total Registrations', 'Teams'],
            ]
            
            # Add event stats
            for event_name, count in stats_data.get('by_event', {}).items():
                rows.append([event_name, count.get('count', 0), count.get('teams', 0)])
            
            # Add workshop stats
            rows.extend([
                [],
                ['WORKSHOPS'],
                ['Workshop Name', 'Total Registrations'],
            ])
            
            for workshop_name, count in stats_data.get('by_workshop', {}).items():
                rows.append([workshop_name, count.get('count', 0)])
            
            # Add college stats
            rows.extend([
                [],
                ['BY COLLEGE'],
                ['College Name', 'Total Registrations'],
            ])
            
            for college_name, count in stats_data.get('by_college', {}).items():
                rows.append([college_name, count])
            
            # Clear and update Stats tab
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range='Stats Dashboard!A:D'
            ).execute()
            
            body = {
                'values': rows
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='Stats Dashboard!A1',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print("✓ Stats dashboard updated")
            return True
            
        except Exception as e:
            print(f"ERROR updating stats dashboard: {str(e)}")
            return False


# Singleton instance
_sheets_service = None

def get_google_sheets_service():
    """Get or create Google Sheets service singleton."""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = GoogleSheetsService()
    return _sheets_service
