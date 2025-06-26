import re
# import dateparser  # Comentado temporariamente
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
import logging

logger = logging.getLogger(__name__)

class NaturalLanguageProcessor:
    def __init__(self):
        self.timezone = pytz.timezone('America/Sao_Paulo')
        
        # Padrões para detectar agendamentos
        self.appointment_patterns = [
            r'quero agendar',
            r'marcar consulta',
            r'agendar consulta',
            r'quero marcar',
            r'gostaria de agendar',
            r'preciso agendar',
            r'pode agendar',
            r'vou agendar',
            r'quero uma consulta',
            r'quero para.*\d',  # "quero para amanha as 14"
            r'quero.*para.*\d',  # "quero marcar para quinta as 15"
            r'quero.*\d.*horas?',  # "quero as 14 horas"
            r'quero.*(?:amanha|hoje|quinta|sexta|segunda|terca|quarta|sabado|domingo).*\d',  # "quero amanha as 18"
            r'quero.*\d+',  # "quero as 18", "quero 15h"
            r'marcar.*para.*\d',  # "marcar para amanha as 14"
            r'agendar.*para.*\d',  # "agendar para quinta 15h"
            r'consulta.*\d.*h',  # "consulta amanha 14h"
            r'posso.*para.*\d',  # "posso para quinta as 14"
            r'tem.*vaga.*\d',  # "tem vaga as 14h"
            r'disponibilidade.*\d',  # "disponibilidade as 15h"
            r'as?\s+\d{1,2}.*(?:tem|livre|disponível)',  # "as 10 tem?" "as 14 tá livre?"
            r'\d{1,2}.*(?:da\s+)?(?:manhã|tarde|noite).*tem',  # "10 da manha tem?"
            r'tem.*as?\s+\d{1,2}',  # "tem as 10?"
            r'pode.*as?\s+\d{1,2}',  # "pode as 15?"
            r'funciona.*as?\s+\d{1,2}',  # "funciona as 14?"
            r'dá.*as?\s+\d{1,2}',  # "dá as 16?"
            r'serve.*as?\s+\d{1,2}',  # "serve as 09?"
            r'\d{1,2}h.*(?:tem|livre|pode)',  # "15h tem?" "14h pode?"
            r'(?:às|as)\s+\d{1,2}.*\?',  # "às 10?" "as 15?"
            # Novos padrões mais amplos
            r'(?:amanha|hoje|quinta|sexta|segunda|terca|quarta|sabado|domingo).*as?\s*\d+',  # "amanha as 18"
            r'(?:amanha|hoje|quinta|sexta|segunda|terca|quarta|sabado|domingo).*\d+h?',  # "amanha 18h"
            r'\d+.*(?:amanha|hoje|quinta|sexta|segunda|terca|quarta|sabado|domingo)',  # "18 amanha"
        ]
        
        # Padrões para horários
        self.time_patterns = [
            r'(\d{1,2})[h:](\d{2})?',  # 14h30, 14:30
            r'(\d{1,2})\s?h(?:oras?)?',  # 14h, 14 horas
            r'às\s+(\d{1,2})[h:]?(\d{2})?',  # às 14h, às 14:30
            r'as\s+(\d{1,2})[h:]?(\d{2})?',  # as 14h, as 14:30
            r'(\d{1,2}):(\d{2})',  # 14:30
        ]
        
        # Mapeamento de dias da semana
        self.weekdays = {
            'segunda': 0, 'segunda-feira': 0,
            'terça': 1, 'terca': 1, 'terça-feira': 1, 'terca-feira': 1,
            'quarta': 2, 'quarta-feira': 2,
            'quinta': 3, 'quinta-feira': 3,
            'sexta': 4, 'sexta-feira': 4,
            'sábado': 5, 'sabado': 5,
            'domingo': 6
        }
        
        # Palavras relativas de tempo
        self.relative_dates = {
            'hoje': 0,
            'amanhã': 1, 'amanha': 1,
            'depois de amanhã': 2, 'depois de amanha': 2,
            'próxima semana': 7, 'proxima semana': 7,
            'semana que vem': 7
        }
    
    def extract_appointment_intent(self, text):
        """Detecta se a mensagem tem intenção de agendamento"""
        text_lower = text.lower()
        
        logger.info(f"[NLP] Analisando intenção para: '{text_lower}'")
        
        for pattern in self.appointment_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"[NLP] Padrão detectado: '{pattern}' -> AGENDAMENTO")
                return True
        
        logger.info(f"[NLP] Nenhum padrão de agendamento detectado")
        return False
    
    def extract_datetime(self, text):
        """Extrai data e horário da mensagem usando métodos básicos"""
        text_lower = text.lower()
        
        # Usa apenas métodos manuais por enquanto
        manual_date = self._extract_date_manual(text_lower)
        manual_time = self._extract_time(text_lower)
        
        if manual_date:
            time_to_use = manual_time or datetime.strptime('14:00', '%H:%M').time()
            final_datetime = datetime.combine(manual_date, time_to_use)
            return self.timezone.localize(final_datetime)
        
        return None
    
    def _extract_date_manual(self, text):
        """Extrai data manualmente usando padrões"""
        today = datetime.now().date()
        
        # Verifica palavras relativas
        for word, days_offset in self.relative_dates.items():
            if word in text:
                return today + timedelta(days=days_offset)
        
        # Verifica dias da semana
        for day_name, weekday in self.weekdays.items():
            if day_name in text:
                days_ahead = weekday - today.weekday()
                if days_ahead <= 0:  # Se já passou, pega próxima semana
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        # Padrões de data DD/MM
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})',  # 15/03
            r'dia\s+(\d{1,2})',      # dia 15
            r'no\s+dia\s+(\d{1,2})', # no dia 15
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                if '/' in pattern:
                    day, month = map(int, match.groups())
                    try:
                        year = today.year
                        date = datetime(year, month, day).date()
                        if date < today:
                            date = datetime(year + 1, month, day).date()
                        return date
                    except ValueError:
                        continue
                else:
                    day = int(match.group(1))
                    try:
                        date = datetime(today.year, today.month, day).date()
                        if date < today:
                            # Próximo mês
                            if today.month == 12:
                                date = datetime(today.year + 1, 1, day).date()
                            else:
                                date = datetime(today.year, today.month + 1, day).date()
                        return date
                    except ValueError:
                        continue
        
        return None
    
    def _extract_time(self, text):
        """Extrai horário da mensagem"""
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 2 and match.group(2):
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                    else:
                        hour = int(match.group(1))
                        minute = 0
                    
                    # Validação básica
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return datetime.strptime(f'{hour:02d}:{minute:02d}', '%H:%M').time()
                        
                except (ValueError, IndexError):
                    continue
        
        # Procura por horários escritos por extenso
        time_words = {
            'meio-dia': '12:00',
            'meio dia': '12:00',
            'meia noite': '00:00',
            'uma hora': '13:00',
            'duas horas': '14:00',
            'três horas': '15:00',
            'quatro horas': '16:00',
            'cinco horas': '17:00',
            'manhã': '09:00',
            'tarde': '14:00',
            'noite': '19:00'
        }
        
        for word, time_str in time_words.items():
            if word in text:
                return datetime.strptime(time_str, '%H:%M').time()
        
        return None
    
    def format_confirmation_message(self, client_name, datetime_obj, google_event=None):
        """Gera mensagem de confirmação do agendamento de forma mais humana"""
        date_str = datetime_obj.strftime('%d/%m/%Y')
        time_str = datetime_obj.strftime('%H:%M')
        weekday = datetime_obj.strftime('%A')
        
        weekday_pt = {
            'Monday': 'segunda-feira',
            'Tuesday': 'terça-feira', 
            'Wednesday': 'quarta-feira',
            'Thursday': 'quinta-feira',
            'Friday': 'sexta-feira',
            'Saturday': 'sábado',
            'Sunday': 'domingo'
        }.get(weekday, weekday)
        
        # Determina se é hoje, amanhã ou outro dia
        today = datetime.now().date()
        appointment_date = datetime_obj.date()
        
        if appointment_date == today:
            day_reference = "hoje"
        elif appointment_date == today + timedelta(days=1):
            day_reference = "amanhã"
        else:
            day_reference = f"na {weekday_pt} ({date_str})"
        
        # Converte horário para linguagem mais natural
        hour = datetime_obj.hour
        if hour < 12:
            time_period = "da manhã"
        elif hour < 18:
            time_period = "da tarde"
        else:
            time_period = "da noite"
        
        message = f"""Pronto, {client_name}! Agendamento confirmado! ✅

Sua consulta ficou marcada para {day_reference} às {time_str} {time_period}.

Valor: R$ 620,00

Só alguns lembretes importantes:
• Chega uns 15 minutinhos antes, tá?
• Traz um documento com foto
• Se rolar algum imprevisto, me avisa o quanto antes

Vou te mandar lembrete 1 dia antes e também 1 hora antes da consulta.

Qualquer coisa é só falar comigo! 😊"""

        if google_event:
            message += f"\n\n_ID do agendamento: {google_event.get('id', 'N/A')}_"
        
        return message
    
    def suggest_alternatives(self, requested_datetime, available_slots):
        """Sugere horários alternativos quando o solicitado não está disponível"""
        date_str = requested_datetime.strftime('%d/%m/%Y')
        time_str = requested_datetime.strftime('%H:%M')
        
        message = f"""😔 Infelizmente o horário {time_str} do dia {date_str} não está disponível.

Mas tenho ótimas opções para você! ⏰

*Horários disponíveis para {date_str}:*"""
        
        for slot in available_slots:
            message += f"\n• {slot}"
        
        message += "\n\nQual horário funciona melhor para você? 🌸"
        
        return message 