import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.conf import settings
import logging
from django.utils import timezone
import pytz
from typing import List, Dict, Optional
from core.models import GoogleCalendarCredentials, GoogleCalendarSettings
import json
from google_auth_oauthlib.flow import Flow
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Serviço real do Google Calendar com autenticação OAuth2"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.calendar_id = 'primary'
        
    def get_auth_url(self) -> str:
        """Gera URL de autenticação OAuth2 para conectar Google Calendar"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=settings.GOOGLE_CALENDAR_SCOPES
            )
            
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info(f"URL de autenticação Google gerada: {auth_url}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autenticação: {e}")
            return None
    
    def exchange_code_for_credentials(self, code: str, user) -> bool:
        """Troca o código de autorização por credenciais e salva no banco"""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=settings.GOOGLE_CALENDAR_SCOPES
            )
            
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Salva ou atualiza as credenciais no banco
            google_creds, created = GoogleCalendarCredentials.objects.get_or_create(
                user=user,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                    'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    'scopes': list(credentials.scopes) if credentials.scopes else [],
                    'expiry': credentials.expiry,
                    'is_active': True
                }
            )
            
            if not created:
                google_creds.access_token = credentials.token
                google_creds.refresh_token = credentials.refresh_token
                google_creds.expiry = credentials.expiry
                google_creds.is_active = True
                google_creds.save()
            
            logger.info(f"Credenciais Google salvas para usuário: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao trocar código por credenciais: {e}")
            return False
    
    def load_credentials(self, user) -> bool:
        """Carrega credenciais do banco e inicializa o serviço"""
        try:
            google_creds = GoogleCalendarCredentials.objects.get(user=user, is_active=True)
            
            self.credentials = Credentials(
                token=google_creds.access_token,
                refresh_token=google_creds.refresh_token,
                token_uri=google_creds.token_uri,
                client_id=google_creds.client_id,
                client_secret=google_creds.client_secret,
                scopes=google_creds.scopes
            )
            
            # Inicializa o serviço
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            # Verifica se as credenciais ainda são válidas
            calendars = self.service.calendarList().list().execute()
            
            logger.info(f"Credenciais Google carregadas para: {user.username}")
            return True
            
        except GoogleCalendarCredentials.DoesNotExist:
            logger.warning(f"Usuário {user.username} não possui credenciais Google")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais Google: {e}")
            return False
    
    def check_availability(self, start_datetime: datetime, end_datetime: datetime) -> bool:
        """Verifica se o horário está disponível no Google Calendar"""
        if not self.service:
            logger.warning("Serviço Google Calendar não inicializado")
            return True  # Fallback para permitir agendamento
        
        try:
            # Formata as datas para RFC3339 - remove timezone info e adiciona Z
            if start_datetime.tzinfo:
                start_utc = start_datetime.utctimetuple()
                time_min = datetime(*start_utc[:6]).isoformat() + 'Z'
            else:
                time_min = start_datetime.isoformat() + 'Z'
                
            if end_datetime.tzinfo:
                end_utc = end_datetime.utctimetuple()
                time_max = datetime(*end_utc[:6]).isoformat() + 'Z'
            else:
                time_max = end_datetime.isoformat() + 'Z'
            
            # Busca eventos no período
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Se não há eventos, o horário está livre
            available = len(events) == 0
            
            logger.info(f"Verificação disponibilidade {start_datetime}: {'Livre' if available else 'Ocupado'}")
            return available
            
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return True  # Fallback para permitir agendamento
    
    def create_appointment(self, client_name: str, client_phone: str, 
                          start_datetime: datetime, end_datetime: datetime, 
                          description: str = "") -> Optional[Dict]:
        """Cria um evento no Google Calendar"""
        if not self.service:
            logger.warning("Serviço Google Calendar não inicializado")
            return None
        
        try:
            event = {
                'summary': f'Consulta - {client_name}',
                'description': f'{description}\n\nCliente: {client_name}\nTelefone: {client_phone}',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'attendees': [
                    {'email': 'dra.elisa@clinica.com'},  # Email da doutora
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                        {'method': 'popup', 'minutes': 60},       # 1 hora antes
                    ],
                },
                'colorId': '2',  # Verde para consultas
            }
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            logger.info(f"Evento criado no Google Calendar: {created_event.get('id')}")
            return created_event
            
        except Exception as e:
            logger.error(f"Erro ao criar evento no Google Calendar: {e}")
            return None
    
    def get_available_slots(self, date, duration_minutes=60) -> List[str]:
        """Busca horários disponíveis em uma data específica"""
        if not self.service:
            logger.warning("Serviço Google Calendar não inicializado")
            return ['14:00', '15:00', '16:00']  # Fallback
        
        try:
            # Configurações padrão
            work_start = datetime.combine(date, datetime.strptime('08:00', '%H:%M').time())
            work_end = datetime.combine(date, datetime.strptime('18:00', '%H:%M').time())
            lunch_start = datetime.combine(date, datetime.strptime('12:00', '%H:%M').time())
            lunch_end = datetime.combine(date, datetime.strptime('14:00', '%H:%M').time())
            
            # Busca eventos do dia
            time_min = work_start.isoformat() + 'Z'
            time_max = work_end.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Gera slots de horário
            available_slots = []
            current_time = work_start
            
            while current_time + timedelta(minutes=duration_minutes) <= work_end:
                # Pula horário de almoço
                if lunch_start <= current_time < lunch_end:
                    current_time = lunch_end
                    continue
                
                # Verifica se o slot está livre
                slot_end = current_time + timedelta(minutes=duration_minutes)
                is_free = True
                
                for event in events:
                    event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    
                    # Converte para timezone local se necessário
                    if event_start.tzinfo:
                        event_start = event_start.replace(tzinfo=None)
                        event_end = event_end.replace(tzinfo=None)
                    
                    # Verifica sobreposição
                    if (current_time < event_end and slot_end > event_start):
                        is_free = False
                        break
                
                if is_free:
                    available_slots.append(current_time.strftime('%H:%M'))
                
                current_time += timedelta(minutes=30)  # Intervalos de 30 min
            
            logger.info(f"Slots disponíveis para {date}: {available_slots}")
            return available_slots[:5]  # Retorna até 5 slots
            
        except Exception as e:
            logger.error(f"Erro ao buscar slots disponíveis: {e}")
            return ['14:00', '15:00', '16:00']  # Fallback
    
    def disconnect(self, user) -> bool:
        """Desconecta e remove credenciais do Google Calendar"""
        try:
            GoogleCalendarCredentials.objects.filter(user=user).update(is_active=False)
            logger.info(f"Credenciais Google removidas para: {user.username}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover credenciais: {e}")
            return False
    
    def get_connection_status(self, user) -> Dict:
        """Verifica status da conexão com Google Calendar"""
        try:
            google_creds = GoogleCalendarCredentials.objects.get(user=user, is_active=True)
            
            # Tenta carregar e usar as credenciais
            if self.load_credentials(user):
                return {
                    'connected': True,
                    'calendar_id': self.calendar_id,
                    'last_sync': google_creds.updated_at,
                    'email': user.email
                }
            else:
                return {'connected': False, 'error': 'Credenciais inválidas'}
                
        except GoogleCalendarCredentials.DoesNotExist:
            return {'connected': False, 'error': 'Não conectado'}
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            return {'connected': False, 'error': str(e)}
    
    def update_appointment(self, event_id, **updates):
        """Atualiza um evento existente"""
        logger.info("Google Calendar desabilitado - mock de atualização")
        return {'id': event_id, 'status': 'updated'}
    
    def cancel_appointment(self, event_id):
        """Cancela um evento no Google Calendar"""
        if not self.service:
            logger.warning("Serviço Google Calendar não inicializado")
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Evento cancelado no Google Calendar: {event_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Evento não encontrado no Google Calendar: {event_id}")
                return True  # Considera sucesso se já foi deletado
            else:
                logger.error(f"Erro HTTP ao cancelar evento: {e}")
                return False
        except Exception as e:
            logger.error(f"Erro ao cancelar evento no Google Calendar: {e}")
            return False 