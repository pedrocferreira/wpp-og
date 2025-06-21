import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../services/api.service';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

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
    DatePipe,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1 class="dashboard-title">
          <mat-icon>dashboard</mat-icon>
          Dashboard de Atendimentos
        </h1>
        <p class="dashboard-subtitle">Gerencie seus atendimentos e clientes em tempo real</p>
      </div>

      <!-- Cards de estatísticas -->
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

    /* Stats Section */
    .stats-section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 12px rgba(107, 70, 193, 0.08);
      border: 1px solid #e2e8f0;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(107, 70, 193, 0.15);
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
    }

    .total-clients-icon {
      background: linear-gradient(135deg, #6b46c1, #8b5cf6);
    }

    .active-clients-icon {
      background: linear-gradient(135deg, #10b981, #34d399);
    }

    .messages-icon {
      background: linear-gradient(135deg, #f59e0b, #fbbf24);
    }

    .appointments-icon {
      background: linear-gradient(135deg, #ef4444, #f87171);
    }

    .stat-icon mat-icon {
      font-size: 24px;
      width: 24px;
      height: 24px;
    }

    .stat-info {
      flex: 1;
    }

    .stat-number {
      font-size: 2rem;
      font-weight: 700;
      color: #1e293b;
      line-height: 1;
    }

    .stat-label {
      color: #64748b;
      font-size: 0.9rem;
      margin-top: 4px;
      font-weight: 500;
    }

    /* Table Section */
    .table-section {
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(107, 70, 193, 0.08);
      border: 1px solid #e2e8f0;
      overflow: hidden;
    }

    .table-header {
      background: linear-gradient(135deg, #6b46c1, #8b5cf6);
      color: white;
      padding: 24px;
    }

    .table-header h2 {
      margin: 0 0 8px 0;
      font-size: 1.5rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .table-header h2 mat-icon {
      font-size: 1.5rem;
      width: 1.5rem;
      height: 1.5rem;
    }

    .table-header p {
      margin: 0;
      opacity: 0.9;
      font-size: 0.95rem;
    }

    .table-content {
      padding: 0;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px;
      gap: 16px;
      color: #64748b;
    }

    /* Custom Table */
    .clients-table {
      width: 100%;
    }

    .table-row {
      display: grid;
      grid-template-columns: 60px 1fr 140px 160px 120px;
      align-items: center;
      padding: 16px 24px;
      border-bottom: 1px solid #f1f5f9;
      transition: background-color 0.2s ease;
    }

    .table-row:hover:not(.table-header-row) {
      background: #f8fafc;
    }

    .table-header-row {
      background: #f8fafc;
      border-bottom: 2px solid #e2e8f0;
      font-weight: 600;
      color: #475569;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .table-cell {
      padding: 0;
    }

    .avatar-cell {
      display: flex;
      justify-content: center;
    }

    .client-avatar mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
      color: #6b46c1;
    }

    .client-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .client-name {
      font-weight: 600;
      color: #1e293b;
      font-size: 0.95rem;
    }

    .client-phone {
      font-size: 0.8rem;
      color: #64748b;
    }

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 500;
    }

    .status-chip.active {
      background: #dcfdf4;
      color: #047857;
    }

    .status-chip.inactive {
      background: #fef2f2;
      color: #dc2626;
    }

    .status-chip mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    .date-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .date {
      font-weight: 500;
      color: #1e293b;
      font-size: 0.9rem;
    }

    .time {
      font-size: 0.8rem;
      color: #64748b;
    }

    .action-buttons {
      display: flex;
      gap: 8px;
    }

    .action-buttons button {
      width: 32px;
      height: 32px;
      line-height: 32px;
    }

    .action-buttons button mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    .empty-state {
      text-align: center;
      padding: 60px 24px;
      color: #64748b;
    }

    .empty-state mat-icon {
      font-size: 4rem;
      width: 4rem;
      height: 4rem;
      color: #cbd5e1;
      margin-bottom: 16px;
    }

    .empty-state h3 {
      color: #475569;
      margin: 0 0 8px 0;
      font-weight: 600;
    }

    .empty-state p {
      margin: 0;
      font-size: 0.9rem;
    }

    /* Responsividade */
    @media (max-width: 1024px) {
      .table-row {
        grid-template-columns: 50px 1fr 120px 140px 100px;
        padding: 12px 16px;
      }
    }

    @media (max-width: 768px) {
      .dashboard-container {
        padding: 16px;
      }

      .dashboard-title {
        font-size: 1.8rem;
        flex-direction: column;
        gap: 8px;
      }

      .stats-section {
        grid-template-columns: 1fr;
        gap: 16px;
      }

      .stat-card {
        padding: 20px;
      }

      .table-row {
        grid-template-columns: 1fr;
        gap: 12px;
        padding: 16px;
      }

      .table-header-row {
        display: none;
      }

      .table-cell {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
      }

      .table-cell:before {
        content: attr(data-label);
        font-weight: 600;
        color: #475569;
        font-size: 0.8rem;
      }

      .avatar-cell:before {
        content: '';
      }

      .action-buttons {
        justify-content: flex-end;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  clients: any[] = [];
  isLoading = true;

  // Estatísticas
  totalClients = 0;
  activeClients = 0;
  pendingMessages = 0;
  todayAppointments = 0;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.apiService.getClients().subscribe({
      next: (data) => {
        this.clients = data;
        this.calculateStats();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erro ao buscar clientes:', err);
        this.isLoading = false;
      }
    });
  }

  calculateStats(): void {
    this.totalClients = this.clients.length;
    this.activeClients = this.clients.filter(client => client.is_active).length;
    this.pendingMessages = Math.floor(Math.random() * 10) + 1;
    this.todayAppointments = Math.floor(Math.random() * 5) + 1;
  }

  verChat(client: any): void {
    console.log('Ver chat do cliente:', client);
    // Futuramente, navegar para a tela de chat com o ID do cliente
  }

  enviarMensagem(client: any): void {
    console.log('Enviar mensagem para:', client);
    // Futuramente, abrir modal para envio de mensagem
  }
} 