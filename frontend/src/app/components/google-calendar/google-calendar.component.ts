import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface GoogleCalendarStatus {
  connected: boolean;
  calendar_id?: string;
  last_sync?: string;
  email?: string;
  error?: string;
}

interface Calendar {
  id: string;
  summary: string;
  primary: boolean;
}

interface CalendarEvent {
  id: string;
  title: string;
  description: string;
  start: string;
  end: string;
  location: string;
  status: string;
  attendees: Array<{
    email: string;
    name: string;
    responseStatus: string;
  }>;
  created: string;
  updated: string;
  htmlLink: string;
  colorId: string;
}

@Component({
  selector: 'app-google-calendar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="calendar-container">
      <h1>🗓️ Integração Google Calendar</h1>
      
      <div class="calendar-card" [ngClass]="{'connected': calendarStatus.connected, 'disconnected': !calendarStatus.connected}">
        
        <!-- Status Conectado -->
        <div *ngIf="calendarStatus.connected" class="connected-state">
          <div class="status-header">
            <h3>✅ Google Calendar Conectado</h3>
            <button class="btn-test" (click)="testConnection()" [disabled]="loading">
              {{loading ? 'Testando...' : 'Testar Conexão'}}
            </button>
          </div>
          
          <div class="connection-info">
            <p><strong>Email:</strong> {{calendarStatus.email}}</p>
            <p><strong>Calendar ID:</strong> {{calendarStatus.calendar_id}}</p>
            <p *ngIf="calendarStatus.last_sync"><strong>Última sincronização:</strong> {{formatDate(calendarStatus.last_sync)}}</p>
          </div>
          
          <div class="calendars-list" *ngIf="availableCalendars.length > 0">
            <h4>Calendários disponíveis:</h4>
            <div class="calendar-item" *ngFor="let calendar of availableCalendars">
              <span class="calendar-name">{{calendar.summary}}</span>
              <span class="calendar-badge" *ngIf="calendar.primary">Principal</span>
            </div>
          </div>
          
          <div class="features-active">
            <h4>Funcionalidades ativas:</h4>
            <ul>
              <li>✅ Agendamentos automáticos via WhatsApp</li>
              <li>✅ Verificação de disponibilidade em tempo real</li>
              <li>✅ Sincronização bidirecional</li>
              <li>✅ Lembretes automáticos</li>
            </ul>
          </div>

          <!-- Seção do Calendário Sincronizado -->
          <div class="calendar-section">
            <div class="calendar-header">
              <h4>📅 Calendário Sincronizado</h4>
              <button class="btn-refresh" (click)="loadCalendarEvents()" [disabled]="loading">
                {{loading ? 'Carregando...' : 'Atualizar'}}
              </button>
            </div>
            
            <div class="calendar-controls">
              <select [(ngModel)]="selectedPeriod" (change)="onPeriodChange()" class="period-select">
                <option value="week">Esta semana</option>
                <option value="month">Este mês</option>
                <option value="next7">Próximos 7 dias</option>
                <option value="next30">Próximos 30 dias</option>
              </select>
            </div>

            <div class="events-container" *ngIf="calendarEvents.length > 0; else noEvents">
              <div class="event-card" *ngFor="let event of calendarEvents" [ngClass]="'color-' + event.colorId">
                <div class="event-header">
                  <h5 class="event-title">{{event.title}}</h5>
                  <span class="event-status" [ngClass]="event.status">{{getEventStatusText(event.status)}}</span>
                </div>
                
                <div class="event-details">
                  <div class="event-time">
                    🕒 {{formatEventDateTime(event.start)}} - {{formatEventTime(event.end)}}
                  </div>
                  
                  <div class="event-description" *ngIf="event.description">
                    📝 {{event.description}}
                  </div>
                  
                  <div class="event-location" *ngIf="event.location">
                    📍 {{event.location}}
                  </div>
                  
                  <div class="event-attendees" *ngIf="event.attendees.length > 0">
                    👥 {{event.attendees.length}} participante(s)
                  </div>
                </div>
                
                <div class="event-actions">
                  <a [href]="event.htmlLink" target="_blank" class="btn-view-google">
                    Ver no Google Calendar
                  </a>
                </div>
              </div>
            </div>

            <ng-template #noEvents>
              <div class="no-events">
                <div class="no-events-icon">📅</div>
                <h4>Nenhum evento encontrado</h4>
                <p>Não há eventos agendados para o período selecionado.</p>
              </div>
            </ng-template>
          </div>
          
          <div class="actions">
            <button class="btn-disconnect" (click)="disconnectCalendar()" [disabled]="loading">
              Desconectar
            </button>
          </div>
        </div>
        
        <!-- Status Desconectado -->
        <div *ngIf="!calendarStatus.connected" class="disconnected-state">
          <div class="status-header">
            <h3>❌ Google Calendar Não Conectado</h3>
          </div>
          
          <p class="status-message">
            Para sincronizar agendamentos automaticamente, conecte sua conta do Google Calendar.
          </p>
          
          <div class="benefits">
            <h4>Benefícios da integração:</h4>
            <ul>
              <li>✅ Agendamentos automáticos via WhatsApp</li>
              <li>✅ Verificação de disponibilidade em tempo real</li>
              <li>✅ Sincronização bidirecional</li>
              <li>✅ Lembretes automáticos</li>
              <li>✅ Integração com outros apps Google</li>
              <li>✅ Backup automático de agendamentos</li>
            </ul>
          </div>
          
          <div class="actions">
            <button class="btn-connect" (click)="connectCalendar()" [disabled]="loading">
              {{loading ? 'Conectando...' : 'Conectar Google Calendar'}}
            </button>
          </div>
        </div>
        
        <!-- Mensagens de status -->
        <div *ngIf="statusMessage" class="status-message" [ngClass]="messageType">
          {{statusMessage}}
        </div>
      </div>
      
      <!-- Instruções -->
      <div class="instructions-card" *ngIf="!calendarStatus.connected">
        <h3>�� Como configurar</h3>
        <ol>
          <li>Clique em "Conectar Google Calendar" acima</li>
          <li>Faça login com sua conta Google</li>
          <li>Autorize o acesso ao seu calendário</li>
          <li>Pronto! Os agendamentos via WhatsApp serão sincronizados automaticamente</li>
        </ol>
        
        <div class="note">
          <strong>Nota:</strong> Você precisa ter uma conta Google e um Google Calendar ativo para usar esta funcionalidade.
        </div>
      </div>
    </div>
  `,
  styles: [`
    .calendar-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }

    h1 {
      text-align: center;
      color: #1f2937;
      margin-bottom: 30px;
      font-size: 2.5em;
    }

    .calendar-card {
      background: white;
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
      border: 3px solid #e5e7eb;
      transition: all 0.3s ease;
      margin-bottom: 30px;
    }

    .calendar-card.connected {
      border-color: #10b981;
      background: linear-gradient(145deg, #ffffff, #f0fdf4);
      box-shadow: 0 10px 25px rgba(16, 185, 129, 0.1);
    }

    .calendar-card.disconnected {
      border-color: #ef4444;
      background: linear-gradient(145deg, #ffffff, #fef2f2);
      box-shadow: 0 10px 25px rgba(239, 68, 68, 0.1);
    }

    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 25px;
    }

    .status-header h3 {
      margin: 0;
      font-size: 1.6em;
      font-weight: 600;
    }

    .connection-info {
      background: #f9fafb;
      padding: 20px;
      border-radius: 12px;
      margin-bottom: 25px;
      border-left: 4px solid #10b981;
    }

    .connection-info p {
      margin: 8px 0;
      color: #374151;
      font-size: 1.1em;
    }

    .calendars-list {
      margin: 25px 0;
    }

    .calendars-list h4 {
      color: #374151;
      margin-bottom: 15px;
    }

    .calendar-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: #f3f4f6;
      border-radius: 8px;
      margin-bottom: 10px;
      transition: background 0.2s ease;
    }

    .calendar-item:hover {
      background: #e5e7eb;
    }

    .calendar-name {
      font-weight: 500;
      color: #1f2937;
    }

    .calendar-badge {
      background: #3b82f6;
      color: white;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.85em;
      font-weight: 500;
    }

    .features-active {
      margin: 25px 0;
      padding: 20px;
      background: #ecfdf5;
      border-radius: 12px;
      border-left: 4px solid #10b981;
    }

    .features-active h4 {
      color: #065f46;
      margin-bottom: 15px;
    }

    .benefits {
      margin: 25px 0;
      padding: 20px;
      background: #fef2f2;
      border-radius: 12px;
      border-left: 4px solid #ef4444;
    }

    .benefits h4 {
      color: #991b1b;
      margin-bottom: 15px;
    }

    .benefits ul, .features-active ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .benefits li, .features-active li {
      padding: 8px 0;
      color: #374151;
      font-size: 1.05em;
    }

    .actions {
      display: flex;
      gap: 15px;
      margin-top: 30px;
      justify-content: center;
    }

    .btn-connect {
      background: linear-gradient(135deg, #4285f4, #34a853);
      color: white;
      border: none;
      padding: 16px 40px;
      border-radius: 12px;
      font-size: 1.1em;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(66, 133, 244, 0.3);
    }

    .btn-connect:hover:not(:disabled) {
      transform: translateY(-3px);
      box-shadow: 0 8px 25px rgba(66, 133, 244, 0.4);
    }

    .btn-disconnect {
      background: #ef4444;
      color: white;
      border: none;
      padding: 12px 25px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
    }

    .btn-disconnect:hover:not(:disabled) {
      background: #dc2626;
      transform: translateY(-2px);
    }

    .btn-test {
      background: #6366f1;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.95em;
      font-weight: 500;
      transition: all 0.3s ease;
    }

    .btn-test:hover:not(:disabled) {
      background: #5b21b6;
      transform: translateY(-2px);
    }

    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none !important;
    }

    .status-message {
      margin-top: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      font-weight: 500;
    }

    .status-message.success {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #10b981;
    }

    .status-message.error {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #ef4444;
    }

    .instructions-card {
      background: white;
      border-radius: 16px;
      padding: 30px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
      border: 2px solid #e5e7eb;
    }

    .instructions-card h3 {
      color: #1f2937;
      margin-bottom: 20px;
      font-size: 1.4em;
    }

    .instructions-card ol {
      padding-left: 20px;
      color: #374151;
      line-height: 1.8;
    }

    .instructions-card li {
      margin-bottom: 10px;
      font-size: 1.05em;
    }

    .note {
      background: #fef3c7;
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid #f59e0b;
      margin-top: 20px;
      color: #92400e;
    }

    /* Estilos do Calendário Sincronizado */
    .calendar-section {
      margin: 30px 0;
      padding: 25px;
      background: #f8fafc;
      border-radius: 12px;
      border: 2px solid #e2e8f0;
    }

    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .calendar-header h4 {
      margin: 0;
      color: #1e293b;
      font-size: 1.3em;
    }

    .btn-refresh {
      background: #3b82f6;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9em;
      transition: all 0.3s ease;
    }

    .btn-refresh:hover:not(:disabled) {
      background: #2563eb;
      transform: translateY(-1px);
    }

    .calendar-controls {
      margin-bottom: 20px;
    }

    .period-select {
      padding: 8px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      background: white;
      font-size: 0.95em;
      cursor: pointer;
    }

    .events-container {
      max-height: 400px;
      overflow-y: auto;
      padding-right: 10px;
    }

    .event-card {
      background: white;
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 15px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      border-left: 4px solid #3b82f6;
      transition: all 0.3s ease;
    }

    .event-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }

    .event-card.color-1 { border-left-color: #3b82f6; }
    .event-card.color-2 { border-left-color: #10b981; }
    .event-card.color-3 { border-left-color: #8b5cf6; }
    .event-card.color-4 { border-left-color: #f59e0b; }
    .event-card.color-5 { border-left-color: #ef4444; }
    .event-card.color-6 { border-left-color: #06b6d4; }
    .event-card.color-7 { border-left-color: #84cc16; }
    .event-card.color-8 { border-left-color: #f97316; }
    .event-card.color-9 { border-left-color: #ec4899; }
    .event-card.color-10 { border-left-color: #6366f1; }
    .event-card.color-11 { border-left-color: #14b8a6; }

    .event-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 15px;
    }

    .event-title {
      margin: 0;
      color: #1e293b;
      font-size: 1.1em;
      font-weight: 600;
      flex: 1;
      margin-right: 10px;
    }

    .event-status {
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.8em;
      font-weight: 500;
      text-transform: capitalize;
    }

    .event-status.confirmed {
      background: #dcfce7;
      color: #166534;
    }

    .event-status.tentative {
      background: #fef3c7;
      color: #92400e;
    }

    .event-status.cancelled {
      background: #fee2e2;
      color: #991b1b;
    }

    .event-details {
      margin-bottom: 15px;
    }

    .event-details > div {
      margin-bottom: 8px;
      color: #475569;
      font-size: 0.95em;
    }

    .event-time {
      font-weight: 500;
      color: #1e293b;
    }

    .event-actions {
      text-align: right;
    }

    .btn-view-google {
      color: #3b82f6;
      text-decoration: none;
      font-size: 0.9em;
      font-weight: 500;
      transition: color 0.3s ease;
    }

    .btn-view-google:hover {
      color: #2563eb;
      text-decoration: underline;
    }

    .no-events {
      text-align: center;
      padding: 40px 20px;
      color: #64748b;
    }

    .no-events-icon {
      font-size: 3em;
      margin-bottom: 15px;
    }

    .no-events h4 {
      margin: 10px 0;
      color: #475569;
    }

    .no-events p {
      margin: 0;
      font-size: 0.95em;
    }

    @media (max-width: 768px) {
      .calendar-container {
        padding: 15px;
      }

      .calendar-card {
        padding: 25px;
      }

      .status-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
      }

      .actions {
        flex-direction: column;
      }

      .btn-connect {
        width: 100%;
      }

      h1 {
        font-size: 2em;
      }
    }
  `]
})
export class GoogleCalendarComponent implements OnInit {
  calendarStatus: GoogleCalendarStatus = { connected: false };
  availableCalendars: Calendar[] = [];
  calendarEvents: CalendarEvent[] = [];
  selectedPeriod: string = 'next7';
  loading = false;
  statusMessage = '';
  messageType: 'success' | 'error' = 'success';

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.checkCalendarStatus();
  }

  async checkCalendarStatus() {
    try {
      const response = await this.apiService.get('/google-calendar/status/');
      this.calendarStatus = response.status;
      
      if (this.calendarStatus.connected) {
        this.showMessage('Google Calendar conectado com sucesso!', 'success');
        // Carrega eventos quando conectado
        await this.loadCalendarEvents();
      }
    } catch (error) {
      console.error('Erro ao verificar status:', error);
      this.calendarStatus = { connected: false, error: 'Erro ao verificar status' };
    }
  }

  async connectCalendar() {
    this.loading = true;
    this.statusMessage = '';
    
    try {
      // Busca URL de autenticação
      const response = await this.apiService.get('/google-calendar/auth-url/');
      
      if (response.success && response.auth_url) {
        this.showMessage('Redirecionando para Google...', 'success');
        
        // Abre popup para autenticação
        const popup = window.open(
          response.auth_url,
          'google-auth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        // Escuta mensagens do popup
        const messageHandler = (event: MessageEvent) => {
          // Aceita mensagens do localhost:9000 e do IP:9000
          const allowedOrigins = [
            'http://localhost:9000',
            'http://155.133.22.207:9000',
            window.location.origin
          ];
          
          if (!allowedOrigins.includes(event.origin)) {
            console.log('Origem não permitida:', event.origin);
            return;
          }
          
          if (event.data.type === 'GOOGLE_AUTH_SUCCESS') {
            popup?.close();
            window.removeEventListener('message', messageHandler);
            this.handleAuthSuccess(event.data.code);
          } else if (event.data.type === 'GOOGLE_AUTH_ERROR') {
            popup?.close();
            window.removeEventListener('message', messageHandler);
            this.showMessage('Erro na autenticação: ' + event.data.error, 'error');
            this.loading = false;
          }
        };
        
        window.addEventListener('message', messageHandler);

        // Verifica se popup foi fechado manualmente
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            this.loading = false;
            this.showMessage('Autenticação cancelada', 'error');
          }
        }, 1000);

      } else {
        this.showMessage('Erro ao gerar URL de autenticação', 'error');
        this.loading = false;
      }
    } catch (error) {
      console.error('Erro ao conectar:', error);
      this.showMessage('Erro ao conectar com Google Calendar', 'error');
      this.loading = false;
    }
  }

  async handleAuthSuccess(code: string) {
    try {
      const response = await this.apiService.post('/google-calendar/callback/', {
        code: code,
        user_id: 1
      });

      if (response.success) {
        this.showMessage('Google Calendar conectado com sucesso!', 'success');
        await this.checkCalendarStatus();
      } else {
        this.showMessage('Erro ao salvar credenciais: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro no callback:', error);
      this.showMessage('Erro ao processar autenticação', 'error');
    } finally {
      this.loading = false;
    }
  }

  async testConnection() {
    this.loading = true;
    try {
      const response = await this.apiService.get('/google-calendar/test/');
      
      if (response.success) {
        this.availableCalendars = response.calendars || [];
        this.showMessage('Conexão testada com sucesso!', 'success');
      } else {
        this.showMessage('Falha no teste: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro no teste:', error);
      this.showMessage('Erro ao testar conexão', 'error');
    } finally {
      this.loading = false;
    }
  }

  async disconnectCalendar() {
    if (!confirm('Tem certeza que deseja desconectar o Google Calendar?')) return;
    
    this.loading = true;
    try {
      const response = await this.apiService.post('/google-calendar/disconnect/', {
        user_id: 1
      });

      if (response.success) {
        this.calendarStatus = { connected: false };
        this.availableCalendars = [];
        this.showMessage('Google Calendar desconectado', 'success');
      } else {
        this.showMessage('Erro ao desconectar: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro ao desconectar:', error);
      this.showMessage('Erro ao desconectar Google Calendar', 'error');
    } finally {
      this.loading = false;
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('pt-BR');
  }

  showMessage(message: string, type: 'success' | 'error') {
    this.statusMessage = message;
    this.messageType = type;
    
    setTimeout(() => {
      this.statusMessage = '';
    }, 5000);
  }

  async loadCalendarEvents() {
    if (!this.calendarStatus.connected) return;
    
    this.loading = true;
    try {
      const { startDate, endDate } = this.getPeriodDates();
      
      const response = await this.apiService.get(
        `/google-calendar/events/?start_date=${startDate}&end_date=${endDate}`
      );
      
      if (response.success) {
        this.calendarEvents = response.events || [];
        this.showMessage(`${this.calendarEvents.length} eventos carregados`, 'success');
      } else {
        this.showMessage('Erro ao carregar eventos: ' + response.message, 'error');
        this.calendarEvents = [];
      }
    } catch (error) {
      console.error('Erro ao carregar eventos:', error);
      this.showMessage('Erro ao carregar eventos do calendário', 'error');
      this.calendarEvents = [];
    } finally {
      this.loading = false;
    }
  }

  onPeriodChange() {
    this.loadCalendarEvents();
  }

  getPeriodDates(): { startDate: string, endDate: string } {
    const now = new Date();
    let startDate: Date;
    let endDate: Date;

    switch (this.selectedPeriod) {
      case 'week':
        const dayOfWeek = now.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + mondayOffset);
        endDate = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + 6);
        break;
      
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        break;
      
      case 'next7':
        startDate = new Date(now);
        endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 7);
        break;
      
      case 'next30':
      default:
        startDate = new Date(now);
        endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 30);
        break;
    }

    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0]
    };
  }

  formatEventDateTime(dateTimeString: string): string {
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleDateString('pt-BR', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateTimeString;
    }
  }

  formatEventTime(dateTimeString: string): string {
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateTimeString;
    }
  }

  getEventStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'confirmed': 'Confirmado',
      'tentative': 'Tentativo',
      'cancelled': 'Cancelado'
    };
    return statusMap[status] || status;
  }
} 