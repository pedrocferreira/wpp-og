import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { interval, Subscription } from 'rxjs';

@Component({
  selector: 'app-analytics-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatChipsModule
  ],
  template: `
    <div class="analytics-container">
      
      <!-- Header -->
      <div class="analytics-header">
        <div class="title-section">
          <h1>
            <mat-icon>analytics</mat-icon>
            Analytics Avançado
          </h1>
          <p>Dashboard em tempo real com insights detalhados</p>
        </div>
        
        <div class="refresh-section">
          <div class="last-update" [class.updating]="isLoading">
            <mat-icon>{{isLoading ? 'sync' : 'check_circle'}}</mat-icon>
            <span>{{isLoading ? 'Atualizando...' : 'Atualizado há ' + lastUpdateTime}}</span>
          </div>
          <button mat-raised-button color="primary" (click)="refreshData()" [disabled]="isLoading">
            <mat-icon>refresh</mat-icon>
            Atualizar
          </button>
        </div>
      </div>

      <!-- Cards de Métricas -->
      <div class="metrics-grid" *ngIf="analyticsData">
        
        <!-- Agendamentos -->
        <div class="metric-card agendamentos">
          <div class="metric-header">
            <div class="metric-icon">
              <mat-icon>event</mat-icon>
            </div>
            <div class="metric-title">Agendamentos</div>
          </div>
          <div class="metric-content">
            <div class="primary-value">{{analyticsData.overview?.appointments?.today || 0}}</div>
            <div class="secondary-value">hoje</div>
            <div class="metric-details">
              <div class="detail-item">
                <span>Esta semana:</span>
                <span>{{analyticsData.overview?.appointments?.week || 0}}</span>
              </div>
              <div class="detail-item">
                <span>Este mês:</span>
                <span>{{analyticsData.overview?.appointments?.month || 0}}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Mensagens -->
        <div class="metric-card mensagens">
          <div class="metric-header">
            <div class="metric-icon">
              <mat-icon>chat</mat-icon>
            </div>
            <div class="metric-title">Mensagens Elô</div>
          </div>
          <div class="metric-content">
            <div class="primary-value">{{analyticsData.overview?.messages?.today || 0}}</div>
            <div class="secondary-value">hoje</div>
            <div class="metric-details">
              <div class="detail-item">
                <span>Esta semana:</span>
                <span>{{analyticsData.overview?.messages?.week || 0}}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Clientes -->
        <div class="metric-card clientes">
          <div class="metric-header">
            <div class="metric-icon">
              <mat-icon>people</mat-icon>
            </div>
            <div class="metric-title">Clientes Ativos</div>
          </div>
          <div class="metric-content">
            <div class="primary-value">{{analyticsData.overview?.active_clients?.today || 0}}</div>
            <div class="secondary-value">hoje</div>
            <div class="metric-details">
              <div class="detail-item">
                <span>Total:</span>
                <span>{{analyticsData.clients?.total_clients || 0}}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance -->
        <div class="metric-card performance">
          <div class="metric-header">
            <div class="metric-icon">
              <mat-icon>trending_up</mat-icon>
            </div>
            <div class="metric-title">Taxa de Conversão</div>
          </div>
          <div class="metric-content">
            <div class="primary-value">{{analyticsData.performance?.conversion_rate || 0}}%</div>
            <div class="secondary-value">mensagem → agendamento</div>
            <div class="metric-details">
              <div class="detail-item">
                <span>Cancelamentos:</span>
                <span>{{analyticsData.performance?.cancellation_rate || 0}}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Próximos Agendamentos -->
      <mat-card class="upcoming-appointments" *ngIf="analyticsData?.appointments?.upcoming_appointments">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>event_upcoming</mat-icon>
            Próximos Agendamentos ({{getUpcomingCount()}})
          </mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="appointments-list">
            <div 
              *ngFor="let appointment of getUpcomingAppointments()" 
              class="appointment-item">
              <div class="appointment-time">
                <div class="time">{{formatTime(appointment.datetime)}}</div>
                <div class="date">{{formatDate(appointment.datetime)}}</div>
              </div>
              <div class="appointment-client">
                <div class="client-name">{{appointment.client_name}}</div>
                <div class="client-phone">{{appointment.client_whatsapp}}</div>
              </div>
              <div class="appointment-status">
                <mat-chip [class]="'chip-' + appointment.status">{{getStatusLabel(appointment.status)}}</mat-chip>
                <mat-chip *ngIf="appointment.has_reminders" class="chip-reminder">
                  <mat-icon>alarm</mat-icon>
                  Lembrete
                </mat-chip>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Loading -->
      <div class="loading-overlay" *ngIf="isLoading">
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
      </div>

      <!-- Erro ou não autenticado -->
      <div class="error-message" *ngIf="errorMessage">
        <mat-icon>error</mat-icon>
        <p>{{errorMessage}}</p>
        <button mat-button (click)="handleError()" color="primary">
          {{errorMessage.includes('token') ? 'Fazer Login' : 'Tentar Novamente'}}
        </button>
      </div>

    </div>
  `,
  styleUrls: ['./analytics-dashboard.component.scss']
})
export class AnalyticsDashboardComponent implements OnInit, OnDestroy {
  analyticsData: any = null;
  isLoading = false;
  lastUpdateTime = '';
  errorMessage = '';
  private refreshSubscription?: Subscription;

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    // Verifica se está autenticado antes de carregar dados
    this.checkAuthAndLoadData();
    this.setupAutoRefresh();
  }

  ngOnDestroy() {
    this.refreshSubscription?.unsubscribe();
  }

  checkAuthAndLoadData() {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      this.errorMessage = 'Você precisa estar logado para ver os analytics. Clique para fazer login.';
      return;
    }
    this.loadAnalyticsData();
  }

  async loadAnalyticsData() {
    this.isLoading = true;
    this.errorMessage = '';
    try {
      this.analyticsData = await this.apiService.get('/appointments/analytics/dashboard/');
      this.lastUpdateTime = new Date().toLocaleTimeString();
    } catch (error: any) {
      console.error('Erro ao carregar analytics:', error);
      if (error.status === 401) {
        this.errorMessage = 'Sessão expirada. Faça login novamente para continuar.';
      } else {
        this.errorMessage = 'Erro ao carregar dados de analytics. Tente novamente.';
      }
    } finally {
      this.isLoading = false;
    }
  }

  setupAutoRefresh() {
    // Atualiza a cada 5 minutos
    this.refreshSubscription = interval(300000).subscribe(() => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        this.loadAnalyticsData();
      }
    });
  }

  refreshData() {
    this.checkAuthAndLoadData();
  }

  handleError() {
    if (this.errorMessage.includes('token') || this.errorMessage.includes('login') || this.errorMessage.includes('Sessão')) {
      // Remove tokens inválidos e redireciona para login
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      this.router.navigate(['/login']);
    } else {
      // Tenta novamente
      this.refreshData();
    }
  }

  getUpcomingAppointments(): any[] {
    return this.analyticsData?.appointments?.upcoming_appointments || [];
  }

  getUpcomingCount(): number {
    return this.getUpcomingAppointments().length;
  }

  getStatusLabel(status: string): string {
    const labels: { [key: string]: string } = {
      'scheduled': 'Agendado',
      'confirmed': 'Confirmado', 
      'cancelled': 'Cancelado',
      'completed': 'Concluído',
      'no_show': 'Não Compareceu'
    };
    return labels[status] || status;
  }

  formatTime(datetime: string): string {
    return new Date(datetime).toLocaleTimeString('pt-BR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  formatDate(datetime: string): string {
    return new Date(datetime).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit'
    });
  }
} 