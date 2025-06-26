import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTabsModule } from '@angular/material/tabs';
import { ApiService } from '../../services/api.service';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { FormBuilder } from '@angular/forms';

interface GoogleCalendarStatus {
  connected: boolean;
  calendar_id?: string;
  last_sync?: string;
  email?: string;
  error?: string;
}

interface AISettings {
  assistant_name: string;
  personality: string;
  clinic_info: string;
  doctor_name: string;
  doctor_specialties: string[];
  working_hours: string;
  appointment_duration: number;
  response_style: string;
  use_emojis: boolean;
  auto_scheduling: boolean;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatBadgeModule,
    MatTooltipModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatExpansionModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    FormsModule,
    DatePipe
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1 class="dashboard-title">
          <mat-icon>dashboard</mat-icon>
          Dashboard de Atendimentos
        </h1>
        <p class="dashboard-subtitle">Gerencie seus atendimentos, configurações e integrações</p>
      </div>

      <!-- Tabs principais -->
      <mat-tab-group class="main-tabs" [(selectedIndex)]="selectedTabIndex">
        
        <!-- Tab 1: Visão Geral -->
        <mat-tab label="Visão Geral">
          <div class="tab-content">
            
            <!-- Estatísticas em Tempo Real -->
            <div class="real-time-stats" *ngIf="systemStats">
              <div class="stats-header">
                <h2>
                  <mat-icon>analytics</mat-icon>
                  Estatísticas em Tempo Real
                </h2>
                <div class="update-indicator" [class.loading]="statsLoading">
                  <mat-icon>{{statsLoading ? 'refresh' : 'check_circle'}}</mat-icon>
                  <span>{{statsLoading ? 'Atualizando...' : 'Atualizado'}}</span>
                </div>
              </div>
              
              <!-- Métricas principais -->
              <div class="main-metrics">
                <div class="metric-card appointments">
                  <div class="metric-icon">
                    <mat-icon>event</mat-icon>
                  </div>
                  <div class="metric-content">
                    <div class="metric-title">Agendamentos</div>
                    <div class="metric-values">
                      <div class="primary-value">{{systemStats.appointments?.today || 0}}</div>
                      <div class="secondary-value">Hoje</div>
                    </div>
                    <div class="metric-breakdown">
                      <span>Semana: {{systemStats.appointments?.this_week || 0}}</span>
                      <span>Mês: {{systemStats.appointments?.this_month || 0}}</span>
                      <span>Total: {{systemStats.appointments?.total || 0}}</span>
                    </div>
                  </div>
                </div>
                
                <div class="metric-card messages">
                  <div class="metric-icon">
                    <mat-icon>message</mat-icon>
                  </div>
                  <div class="metric-content">
                    <div class="metric-title">Mensagens WhatsApp</div>
                    <div class="metric-values">
                      <div class="primary-value">{{systemStats.messages?.today || 0}}</div>
                      <div class="secondary-value">Hoje</div>
                    </div>
                    <div class="metric-breakdown">
                      <span>Recebidas: {{systemStats.messages?.incoming_today || 0}}</span>
                      <span>Enviadas: {{systemStats.messages?.outgoing_today || 0}}</span>
                      <span>Semana: {{systemStats.messages?.this_week || 0}}</span>
                    </div>
                  </div>
                </div>
                
                <div class="metric-card clients">
                  <div class="metric-icon">
                    <mat-icon>people</mat-icon>
                  </div>
                  <div class="metric-content">
                    <div class="metric-title">Clientes Únicos</div>
                    <div class="metric-values">
                      <div class="primary-value">{{systemStats.clients?.unique_today || 0}}</div>
                      <div class="secondary-value">Hoje</div>
                    </div>
                    <div class="metric-breakdown">
                      <span>Esta semana: {{systemStats.clients?.unique_week || 0}}</span>
                    </div>
                  </div>
                </div>
                
                <div class="metric-card performance">
                  <div class="metric-icon">
                    <mat-icon>trending_up</mat-icon>
                  </div>
                  <div class="metric-content">
                    <div class="metric-title">Taxa de Conversão</div>
                    <div class="metric-values">
                      <div class="primary-value">{{systemStats.performance?.conversion_rate || 0}}%</div>
                      <div class="secondary-value">Mensagens → Agendamentos</div>
                    </div>
                    <div class="metric-breakdown">
                      <span class="{{getStatusColor(systemStats.performance?.ai_status || '')}}">
                        IA: {{systemStats.performance?.ai_status || 'Desconhecido'}}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Status das Integrações -->
              <div class="integrations-status">
                <div class="integration-item">
                  <mat-icon [class]="systemStats.integrations?.google_calendar?.connected ? 'text-green-600' : 'text-red-600'">
                    {{systemStats.integrations?.google_calendar?.connected ? 'check_circle' : 'error'}}
                  </mat-icon>
                  <span>Google Calendar</span>
                  <span class="integration-detail">
                    {{systemStats.integrations?.google_calendar?.connected ? 
                      ('Conectado: ' + systemStats.integrations.google_calendar.email) : 
                      'Desconectado'}}
                  </span>
                </div>
              </div>
              
              <!-- Próximos Agendamentos -->
              <div class="upcoming-appointments" *ngIf="systemStats.appointments?.upcoming?.length > 0">
                <h3>Próximos Agendamentos</h3>
                <div class="upcoming-list">
                  <div class="upcoming-item" *ngFor="let apt of systemStats.appointments.upcoming">
                    <div class="upcoming-icon">
                      <mat-icon>event_note</mat-icon>
                    </div>
                    <div class="upcoming-info">
                      <div class="upcoming-name">{{apt.client_name}}</div>
                      <div class="upcoming-datetime">{{apt.datetime}}</div>
                      <div class="upcoming-meta">
                        <span class="source-badge" [class]="apt.source">{{apt.source}}</span>
                        <span *ngIf="apt.has_google_event" class="google-badge">
                          <mat-icon>calendar_today</mat-icon>
                          Sincronizado
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Erro ao carregar estatísticas -->
            <div class="stats-error" *ngIf="statsError">
              <mat-icon>error</mat-icon>
              <span>{{statsError}}</span>
              <button mat-button (click)="loadSystemStats()">Tentar Novamente</button>
            </div>
            
            <!-- Cards de estatísticas básicas (mantidos para compatibilidade) -->
            <div class="stats-section">
              <div class="stat-card">
                <div class="stat-icon total-clients-icon">
                  <mat-icon>people</mat-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{totalClients}}</div>
                  <div class="stat-label">Total de Clientes</div>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon active-clients-icon">
                  <mat-icon>person_check</mat-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{activeClients}}</div>
                  <div class="stat-label">Clientes Ativos</div>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon messages-icon">
                  <mat-icon [matBadge]="pendingMessages" matBadgeColor="warn">chat_bubble</mat-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{pendingMessages}}</div>
                  <div class="stat-label">Mensagens Pendentes</div>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon appointments-icon">
                  <mat-icon>event_note</mat-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-number">{{todayAppointments}}</div>
                  <div class="stat-label">Agendamentos Hoje</div>
                </div>
              </div>
            </div>

            <!-- Tabela de clientes -->
            <div class="table-section">
              <div class="table-header">
                <h2>
                  <mat-icon>people_outline</mat-icon>
                  Lista de Clientes
                </h2>
                <p>Gerencie e visualize todos os seus clientes</p>
              </div>

              <div class="table-content">
                <div *ngIf="isLoading" class="loading-container">
                  <mat-spinner diameter="40"></mat-spinner>
                  <span>Carregando dados...</span>
                </div>

                <div *ngIf="!isLoading && clients.length > 0" class="clients-table">
                  <div class="table-row table-header-row">
                    <div class="table-cell avatar-cell"></div>
                    <div class="table-cell">Cliente</div>
                    <div class="table-cell">Status</div>
                    <div class="table-cell">Última Interação</div>
                    <div class="table-cell">Ações</div>
                  </div>

                  <div class="table-row" *ngFor="let client of clients">
                    <div class="table-cell avatar-cell">
                      <div class="client-avatar">
                        <mat-icon>account_circle</mat-icon>
                      </div>
                    </div>
                    
                    <div class="table-cell">
                      <div class="client-info">
                        <div class="client-name">{{client.name}}</div>
                        <div class="client-phone">{{client.phone || 'Não informado'}}</div>
                      </div>
                    </div>
                    
                    <div class="table-cell">
                      <div class="status-chip" [class.active]="client.is_active" [class.inactive]="!client.is_active">
                        <mat-icon>{{client.is_active ? 'check_circle' : 'pause_circle'}}</mat-icon>
                        <span>{{client.is_active ? 'Ativo' : 'Inativo'}}</span>
                      </div>
                    </div>
                    
                    <div class="table-cell">
                      <div class="date-info">
                        <div class="date">{{client.last_interaction | date: 'dd/MM/yyyy'}}</div>
                        <div class="time">{{client.last_interaction | date: 'HH:mm'}}</div>
                      </div>
                    </div>
                    
                    <div class="table-cell">
                      <div class="action-buttons">
                        <button mat-mini-fab color="primary" (click)="verChat(client)" matTooltip="Ver chat">
                          <mat-icon>chat</mat-icon>
                        </button>
                        <button mat-mini-fab color="accent" (click)="enviarMensagem(client)" matTooltip="Enviar mensagem">
                          <mat-icon>send</mat-icon>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div *ngIf="!isLoading && clients.length === 0" class="empty-state">
                  <mat-icon>people_outline</mat-icon>
                  <h3>Nenhum cliente encontrado</h3>
                  <p>Quando você tiver clientes, eles aparecerão aqui.</p>
                </div>
              </div>
            </div>
          </div>
        </mat-tab>

        <!-- Tab 2: Configurações -->
        <mat-tab label="Configurações">
          <div class="tab-content">
            
            <!-- Google Calendar Section -->
            <mat-card class="config-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>calendar_today</mat-icon>
                  Integração Google Calendar
                </mat-card-title>
                <mat-card-subtitle>
                  Conecte seu Google Calendar para agendamentos automáticos
                </mat-card-subtitle>
              </mat-card-header>
              
              <mat-card-content>
                <!-- Status Conectado -->
                <div *ngIf="calendarStatus.connected" class="connection-status connected">
                  <div class="status-header">
                    <div class="status-info">
                      <mat-icon class="status-icon">check_circle</mat-icon>
                      <div>
                        <h3>Google Calendar Conectado</h3>
                        <p>{{calendarStatus.email}}</p>
                      </div>
                    </div>
                    <button mat-stroked-button color="primary" (click)="testCalendarConnection()" [disabled]="loadingCalendar">
                      <mat-icon>refresh</mat-icon>
                      {{loadingCalendar ? 'Testando...' : 'Testar'}}
                    </button>
                  </div>
                  
                  <div class="connection-details">
                    <p><strong>Calendar ID:</strong> {{calendarStatus.calendar_id}}</p>
                    <p *ngIf="calendarStatus.last_sync"><strong>Última sincronização:</strong> {{formatDate(calendarStatus.last_sync)}}</p>
                  </div>
                  
                  <div class="features-list">
                    <h4>Funcionalidades ativas:</h4>
                    <ul>
                      <li><mat-icon>check</mat-icon> Agendamentos automáticos via WhatsApp</li>
                      <li><mat-icon>check</mat-icon> Verificação de disponibilidade em tempo real</li>
                      <li><mat-icon>check</mat-icon> Sincronização bidirecional</li>
                      <li><mat-icon>check</mat-icon> Lembretes automáticos</li>
                    </ul>
                  </div>
                </div>
                
                <!-- Status Desconectado -->
                <div *ngIf="!calendarStatus.connected" class="connection-status disconnected">
                  <div class="status-header">
                    <div class="status-info">
                      <mat-icon class="status-icon">error_outline</mat-icon>
                      <div>
                        <h3>Google Calendar Não Conectado</h3>
                        <p>Para sincronizar agendamentos automaticamente, conecte sua conta</p>
                      </div>
                    </div>
                  </div>
                  
                  <div class="benefits-list">
                    <h4>Benefícios da integração:</h4>
                    <ul>
                      <li><mat-icon>star</mat-icon> Agendamentos automáticos via WhatsApp</li>
                      <li><mat-icon>star</mat-icon> Verificação de disponibilidade em tempo real</li>
                      <li><mat-icon>star</mat-icon> Sincronização com outros dispositivos</li>
                      <li><mat-icon>star</mat-icon> Backup automático de agendamentos</li>
                    </ul>
                  </div>
                </div>
                
                <!-- Mensagem de status -->
                <div *ngIf="calendarMessage" class="status-message" [ngClass]="calendarMessageType">
                  <mat-icon>{{calendarMessageType === 'success' ? 'check_circle' : 'error'}}</mat-icon>
                  {{calendarMessage}}
                </div>
              </mat-card-content>
              
              <mat-card-actions>
                <button *ngIf="!calendarStatus.connected" 
                        mat-raised-button 
                        color="primary" 
                        (click)="connectGoogleCalendar()" 
                        [disabled]="loadingCalendar">
                  <mat-icon>link</mat-icon>
                  {{loadingCalendar ? 'Conectando...' : 'Conectar Google Calendar'}}
                </button>
                
                <button *ngIf="calendarStatus.connected" 
                        mat-stroked-button 
                        color="warn" 
                        (click)="disconnectGoogleCalendar()" 
                        [disabled]="loadingCalendar">
                  <mat-icon>link_off</mat-icon>
                  Desconectar
                </button>
              </mat-card-actions>
            </mat-card>

            <!-- AI Assistant Settings -->
            <mat-card class="config-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>smart_toy</mat-icon>
                  Configurações da IA
                </mat-card-title>
                <mat-card-subtitle>
                  Personalize o comportamento da assistente virtual
                </mat-card-subtitle>
              </mat-card-header>
              
              <mat-card-content>
                <div class="ai-config-form">
                  <!-- Informações básicas -->
                  <mat-expansion-panel>
                    <mat-expansion-panel-header>
                      <mat-panel-title>Informações Básicas</mat-panel-title>
                      <mat-panel-description>Nome e personalidade da assistente</mat-panel-description>
                    </mat-expansion-panel-header>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Nome da Assistente</mat-label>
                        <input matInput [(ngModel)]="aiSettings.assistant_name" placeholder="Ex: Elô">
                        <mat-icon matSuffix>badge</mat-icon>
                      </mat-form-field>
                    </div>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Personalidade</mat-label>
                        <textarea matInput 
                                  [(ngModel)]="aiSettings.personality" 
                                  placeholder="Descreva como a assistente deve se comportar"
                                  rows="3"></textarea>
                        <mat-icon matSuffix>psychology</mat-icon>
                      </mat-form-field>
                    </div>
                  </mat-expansion-panel>

                  <!-- Informações da clínica -->
                  <mat-expansion-panel>
                    <mat-expansion-panel-header>
                      <mat-panel-title>Informações da Clínica</mat-panel-title>
                      <mat-panel-description>Dados do consultório e médico</mat-panel-description>
                    </mat-expansion-panel-header>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Nome do(a) Médico(a)</mat-label>
                        <input matInput [(ngModel)]="aiSettings.doctor_name" placeholder="Ex: Dra. Elisa Munaretti">
                        <mat-icon matSuffix>person</mat-icon>
                      </mat-form-field>
                    </div>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Especialidades</mat-label>
                        <mat-select [(ngModel)]="aiSettings.doctor_specialties" multiple>
                          <mat-option value="psicologia">Psicologia</mat-option>
                          <mat-option value="psiquiatria">Psiquiatria</mat-option>
                          <mat-option value="terapia">Terapia</mat-option>
                          <mat-option value="coaching">Coaching</mat-option>
                        </mat-select>
                        <mat-icon matSuffix>medical_services</mat-icon>
                      </mat-form-field>
                    </div>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Informações da Clínica</mat-label>
                        <textarea matInput 
                                  [(ngModel)]="aiSettings.clinic_info" 
                                  placeholder="Descreva a clínica, localização, abordagem, etc."
                                  rows="4"></textarea>
                        <mat-icon matSuffix>business</mat-icon>
                      </mat-form-field>
                    </div>
                  </mat-expansion-panel>

                  <!-- Configurações de atendimento -->
                  <mat-expansion-panel>
                    <mat-expansion-panel-header>
                      <mat-panel-title>Configurações de Atendimento</mat-panel-title>
                      <mat-panel-description>Horários e duração das consultas</mat-panel-description>
                    </mat-expansion-panel-header>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline">
                        <mat-label>Horário de Funcionamento</mat-label>
                        <input matInput [(ngModel)]="aiSettings.working_hours" placeholder="Ex: Seg-Sex 8h-18h, Sáb 8h-13h">
                        <mat-icon matSuffix>schedule</mat-icon>
                      </mat-form-field>
                      
                      <mat-form-field appearance="outline">
                        <mat-label>Duração da Consulta (min)</mat-label>
                        <input matInput type="number" [(ngModel)]="aiSettings.appointment_duration" placeholder="60">
                        <mat-icon matSuffix>timer</mat-icon>
                      </mat-form-field>
                    </div>
                  </mat-expansion-panel>

                  <!-- Estilo de resposta -->
                  <mat-expansion-panel>
                    <mat-expansion-panel-header>
                      <mat-panel-title>Estilo de Resposta</mat-panel-title>
                      <mat-panel-description>Como a IA deve responder aos clientes</mat-panel-description>
                    </mat-expansion-panel-header>
                    
                    <div class="form-row">
                      <mat-form-field appearance="outline" class="full-width">
                        <mat-label>Estilo de Comunicação</mat-label>
                        <mat-select [(ngModel)]="aiSettings.response_style">
                          <mat-option value="formal">Formal e profissional</mat-option>
                          <mat-option value="friendly">Amigável e caloroso</mat-option>
                          <mat-option value="casual">Descontraído e informal</mat-option>
                          <mat-option value="empathetic">Empático e acolhedor</mat-option>
                        </mat-select>
                      </mat-form-field>
                    </div>
                    
                    <div class="form-row toggle-row">
                      <mat-slide-toggle [(ngModel)]="aiSettings.use_emojis">
                        Usar emojis nas respostas
                      </mat-slide-toggle>
                      
                      <mat-slide-toggle [(ngModel)]="aiSettings.auto_scheduling">
                        Agendamento automático
                      </mat-slide-toggle>
                    </div>
                  </mat-expansion-panel>
                </div>
              </mat-card-content>
              
              <mat-card-actions>
                <button mat-raised-button color="primary" (click)="saveAISettings()" [disabled]="loadingAI">
                  <mat-icon>save</mat-icon>
                  {{loadingAI ? 'Salvando...' : 'Salvar Configurações'}}
                </button>
                
                <button mat-stroked-button (click)="resetAISettings()">
                  <mat-icon>refresh</mat-icon>
                  Restaurar Padrão
                </button>
              </mat-card-actions>
            </mat-card>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 24px;
      background: transparent;
      min-height: calc(100vh - 70px);
      font-family: 'Roboto', sans-serif;
    }

    /* Header */
    .dashboard-header {
      text-align: center;
      margin-bottom: 30px;
    }

    .dashboard-title {
      color: #6b46c1;
      font-size: 2.2rem;
      font-weight: 700;
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
    }

    .dashboard-title mat-icon {
      font-size: 2.2rem;
      width: 2.2rem;
      height: 2.2rem;
    }

    .dashboard-subtitle {
      color: #64748b;
      font-size: 1rem;
      margin: 8px 0 0 0;
      font-weight: 400;
    }

    /* Tabs */
    .main-tabs {
      margin-bottom: 20px;
    }

    .tab-content {
      padding: 20px 0;
    }

    /* Stats Section */
    .stats-section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 24px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
    }

    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.2);
    }

    .stat-icon mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
    }

    .stat-info {
      flex: 1;
    }

    .stat-number {
      font-size: 2.2rem;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 0.9rem;
      opacity: 0.9;
      font-weight: 500;
    }

    /* Table Section */
    .table-section {
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      border: 1px solid #e5e7eb;
    }

    .table-header {
      margin-bottom: 24px;
    }

    .table-header h2 {
      color: #1f2937;
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 8px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .table-header p {
      color: #6b7280;
      margin: 0;
    }

    .clients-table {
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #e5e7eb;
    }

    .table-row {
      display: grid;
      grid-template-columns: 60px 1fr 120px 140px 120px;
      align-items: center;
      padding: 16px;
      border-bottom: 1px solid #f3f4f6;
      transition: background-color 0.2s ease;
    }

    .table-row:hover:not(.table-header-row) {
      background-color: #f9fafb;
    }

    .table-header-row {
      background: #f8fafc;
      font-weight: 600;
      color: #374151;
      border-bottom: 2px solid #e5e7eb;
    }

    .table-cell {
      padding: 0 8px;
    }

    .client-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #6b7280;
    }

    .client-info {
      min-width: 0;
    }

    .client-name {
      font-weight: 500;
      color: #1f2937;
      margin-bottom: 2px;
    }

    .client-phone {
      font-size: 0.85rem;
      color: #6b7280;
    }

    .status-chip {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 500;
    }

    .status-chip.active {
      background: #dcfce7;
      color: #166534;
    }

    .status-chip.inactive {
      background: #fef2f2;
      color: #991b1b;
    }

    .status-chip mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    .date-info {
      text-align: center;
    }

    .date {
      font-weight: 500;
      color: #1f2937;
      margin-bottom: 2px;
    }

    .time {
      font-size: 0.85rem;
      color: #6b7280;
    }

    .action-buttons {
      display: flex;
      gap: 8px;
      justify-content: center;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      padding: 40px;
      color: #6b7280;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: #6b7280;
    }

    .empty-state mat-icon {
      font-size: 4rem;
      width: 4rem;
      height: 4rem;
      margin-bottom: 16px;
      opacity: 0.5;
    }

    .empty-state h3 {
      margin: 0 0 8px 0;
      color: #374151;
    }

    .empty-state p {
      margin: 0;
    }

    /* Config Cards */
    .config-card {
      margin-bottom: 24px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .config-card mat-card-header {
      padding-bottom: 16px;
    }

    .config-card mat-card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 1.3rem;
    }

    /* Google Calendar Status */
    .connection-status {
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 16px;
    }

    .connection-status.connected {
      background: linear-gradient(135deg, #ecfdf5, #d1fae5);
      border: 1px solid #10b981;
    }

    .connection-status.disconnected {
      background: linear-gradient(135deg, #fef2f2, #fee2e2);
      border: 1px solid #ef4444;
    }

    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .status-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .status-icon {
      font-size: 2rem !important;
      width: 2rem !important;
      height: 2rem !important;
    }

    .connection-status.connected .status-icon {
      color: #10b981;
    }

    .connection-status.disconnected .status-icon {
      color: #ef4444;
    }

    .status-info h3 {
      margin: 0 0 4px 0;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .status-info p {
      margin: 0;
      color: #6b7280;
      font-size: 0.9rem;
    }

    .connection-details {
      background: rgba(255, 255, 255, 0.7);
      padding: 12px;
      border-radius: 6px;
      margin-bottom: 16px;
    }

    .connection-details p {
      margin: 4px 0;
      color: #374151;
      font-size: 0.9rem;
    }

    .features-list, .benefits-list {
      margin-top: 16px;
    }

    .features-list h4, .benefits-list h4 {
      margin: 0 0 8px 0;
      color: #374151;
      font-size: 1rem;
    }

    .features-list ul, .benefits-list ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .features-list li, .benefits-list li {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      color: #374151;
      font-size: 0.9rem;
    }

    .features-list mat-icon {
      color: #10b981;
      font-size: 16px !important;
      width: 16px !important;
      height: 16px !important;
    }

    .benefits-list mat-icon {
      color: #f59e0b;
      font-size: 16px !important;
      width: 16px !important;
      height: 16px !important;
    }

    .status-message {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px;
      border-radius: 6px;
      margin-top: 16px;
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

    /* AI Config Form */
    .ai-config-form {
      margin-top: 16px;
    }

    .ai-config-form mat-expansion-panel {
      margin-bottom: 16px;
      border-radius: 8px !important;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }

    .form-row {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
    }

    .form-row.toggle-row {
      flex-direction: column;
      gap: 12px;
    }

    .full-width {
      flex: 1;
    }

    .form-row mat-form-field {
      flex: 1;
    }

    .form-row mat-slide-toggle {
      margin: 8px 0;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .dashboard-container {
        padding: 16px;
      }

      .stats-section {
        grid-template-columns: 1fr;
      }

      .table-row {
        grid-template-columns: 1fr;
        gap: 8px;
      }

      .table-cell {
        padding: 4px 0;
      }

      .status-header {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
      }

      .form-row {
        flex-direction: column;
      }
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  clients: any[] = [];
  isLoading = true;
  selectedTabIndex = 0;
  totalClients = 0;
  activeClients = 0;
  pendingMessages = 0;
  todayAppointments = 0;

  calendarStatus: GoogleCalendarStatus = { connected: false };
  loadingCalendar = false;
  calendarMessage = '';
  calendarMessageType: 'success' | 'error' = 'success';

  aiSettings: AISettings = {
    assistant_name: 'Elô',
    personality: 'Sou uma assistente calorosa, empática e profissional. Sempre procuro ajudar os clientes da melhor forma possível.',
    clinic_info: 'Clínica especializada em saúde mental e bem-estar, oferecendo atendimento humanizado e personalizado.',
    doctor_name: 'Dra. Elisa Munaretti',
    doctor_specialties: ['psicologia'],
    working_hours: 'Segunda a sexta: 8h às 18h, Sábado: 8h às 13h',
    appointment_duration: 60,
    response_style: 'empathetic',
    use_emojis: true,
    auto_scheduling: true
  };
  loadingAI = false;

  activeTab = 'overview';
  
  // Propriedades para estatísticas
  systemStats: any = null;
  statsLoading = false;
  statsError = '';
  private statsInterval: any;

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder
  ) { }

  ngOnInit(): void {
    this.initForms();
    this.loadDashboardData();
    this.checkCalendarStatus();
    this.loadAISettings();
    
    // Carrega estatísticas iniciais
    this.loadSystemStats();
    
    // Atualiza estatísticas a cada 30 segundos
    this.statsInterval = setInterval(() => {
      this.loadSystemStats();
    }, 30000);
  }

  ngOnDestroy() {
    if (this.statsInterval) {
      clearInterval(this.statsInterval);
    }
  }

  initForms(): void {
    // Initialize any necessary forms
  }

  loadDashboardData(): void {
    this.apiService.get('/clients/').then(response => {
      this.clients = response.results || response || [];
      this.calculateStats();
      this.isLoading = false;
    }).catch(error => {
      console.error('Erro ao carregar dados:', error);
      this.isLoading = false;
    });
  }

  calculateStats(): void {
    this.totalClients = this.clients.length;
    this.activeClients = this.clients.filter(client => client.is_active).length;
    this.pendingMessages = Math.floor(Math.random() * 10);
    this.todayAppointments = Math.floor(Math.random() * 5);
  }

  verChat(client: any): void {
    console.log('Ver chat do cliente:', client);
  }

  enviarMensagem(client: any): void {
    console.log('Enviar mensagem para:', client);
  }

  async checkCalendarStatus() {
    try {
      const response = await this.apiService.get('/google-calendar/status/');
      this.calendarStatus = response.status;
    } catch (error) {
      console.error('Erro ao verificar status:', error);
      this.calendarStatus = { connected: false, error: 'Erro ao verificar status' };
    }
  }

  async connectGoogleCalendar() {
    this.loadingCalendar = true;
    this.calendarMessage = '';
    
    try {
      const response = await this.apiService.get('/google-calendar/auth-url/');
      
      if (response.success && response.auth_url) {
        this.showCalendarMessage('Redirecionando para Google...', 'success');
        
        const popup = window.open(
          response.auth_url,
          'google-auth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        window.addEventListener('message', (event) => {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'GOOGLE_AUTH_SUCCESS') {
            popup?.close();
            this.handleAuthSuccess(event.data.code);
          } else if (event.data.type === 'GOOGLE_AUTH_ERROR') {
            popup?.close();
            this.showCalendarMessage('Erro na autenticação: ' + event.data.error, 'error');
            this.loadingCalendar = false;
          }
        });

        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            this.loadingCalendar = false;
            this.showCalendarMessage('Autenticação cancelada', 'error');
          }
        }, 1000);

      } else {
        this.showCalendarMessage('Erro ao gerar URL de autenticação', 'error');
        this.loadingCalendar = false;
      }
    } catch (error) {
      console.error('Erro ao conectar:', error);
      this.showCalendarMessage('Erro ao conectar com Google Calendar', 'error');
      this.loadingCalendar = false;
    }
  }

  async handleAuthSuccess(code: string) {
    try {
      const response = await this.apiService.post('/google-calendar/callback/', {
        code: code,
        user_id: 1
      });

      if (response.success) {
        this.showCalendarMessage('Google Calendar conectado com sucesso!', 'success');
        await this.checkCalendarStatus();
      } else {
        this.showCalendarMessage('Erro ao salvar credenciais: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro no callback:', error);
      this.showCalendarMessage('Erro ao processar autenticação', 'error');
    } finally {
      this.loadingCalendar = false;
    }
  }

  async testCalendarConnection() {
    this.loadingCalendar = true;
    try {
      const response = await this.apiService.get('/google-calendar/test/');
      
      if (response.success) {
        this.showCalendarMessage('Conexão testada com sucesso!', 'success');
      } else {
        this.showCalendarMessage('Falha no teste: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro no teste:', error);
      this.showCalendarMessage('Erro ao testar conexão', 'error');
    } finally {
      this.loadingCalendar = false;
    }
  }

  async disconnectGoogleCalendar() {
    if (!confirm('Tem certeza que deseja desconectar o Google Calendar?')) return;
    
    this.loadingCalendar = true;
    try {
      const response = await this.apiService.post('/google-calendar/disconnect/', {
        user_id: 1
      });

      if (response.success) {
        this.calendarStatus = { connected: false };
        this.showCalendarMessage('Google Calendar desconectado', 'success');
      } else {
        this.showCalendarMessage('Erro ao desconectar: ' + response.message, 'error');
      }
    } catch (error) {
      console.error('Erro ao desconectar:', error);
      this.showCalendarMessage('Erro ao desconectar Google Calendar', 'error');
    } finally {
      this.loadingCalendar = false;
    }
  }

  showCalendarMessage(message: string, type: 'success' | 'error') {
    this.calendarMessage = message;
    this.calendarMessageType = type;
    
    setTimeout(() => {
      this.calendarMessage = '';
    }, 5000);
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('pt-BR');
  }

  async loadAISettings() {
    try {
      const response = await this.apiService.get('/ai-settings/?user_id=1');
      
      if (response.success && response.settings) {
        this.aiSettings = response.settings;
      }
    } catch (error) {
      console.error('Erro ao carregar configurações da IA:', error);
    }
  }

  async saveAISettings() {
    this.loadingAI = true;
    try {
      const response = await this.apiService.post('/ai-settings/save/', {
        user_id: 1,
        ...this.aiSettings
      });
      
      if (response.success) {
        alert('Configurações da IA salvas com sucesso!');
        this.aiSettings = response.settings;
      } else {
        alert('Erro ao salvar: ' + response.message);
      }
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
      alert('Erro ao salvar configurações');
    } finally {
      this.loadingAI = false;
    }
  }

  resetAISettings() {
    if (confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
      this.aiSettings = {
        assistant_name: 'Elô',
        personality: 'Sou uma assistente calorosa, empática e profissional. Sempre procuro ajudar os clientes da melhor forma possível.',
        clinic_info: 'Clínica especializada em saúde mental e bem-estar, oferecendo atendimento humanizado e personalizado.',
        doctor_name: 'Dra. Elisa Munaretti',
        doctor_specialties: ['psicologia'],
        working_hours: 'Segunda a sexta: 8h às 18h, Sábado: 8h às 13h',
        appointment_duration: 60,
        response_style: 'empathetic',
        use_emojis: true,
        auto_scheduling: true
      };
    }
  }

  async loadSystemStats() {
    this.statsLoading = true;
    this.statsError = '';
    
    try {
      const response = await this.apiService.get('/api/system/stats/');
      if (response.success) {
        this.systemStats = response.stats;
        console.log('Estatísticas carregadas:', this.systemStats);
      } else {
        this.statsError = 'Erro ao carregar estatísticas';
      }
    } catch (error: any) {
      console.error('Erro ao carregar estatísticas:', error);
      this.statsError = 'Erro ao conectar com o servidor';
    } finally {
      this.statsLoading = false;
    }
  }
  
  formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('pt-BR');
  }
  
  getStatusColor(status: string): string {
    switch (status) {
      case 'Ativo':
        return 'text-green-600';
      case 'Erro na configuração':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  }
} 