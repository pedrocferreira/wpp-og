import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    MatCardModule,
    MatTableModule,
    MatIconModule,
    MatButtonModule,
    DatePipe
  ],
  template: `
    <div class="dashboard-container">
      <mat-card>
        <mat-card-header>
          <mat-card-title>Atendimentos</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <mat-table [dataSource]="atendimentos">
            <ng-container matColumnDef="cliente">
              <mat-header-cell *matHeaderCellDef>Cliente</mat-header-cell>
              <mat-cell *matCellDef="let atendimento">{{atendimento.cliente}}</mat-cell>
            </ng-container>

            <ng-container matColumnDef="status">
              <mat-header-cell *matHeaderCellDef>Status</mat-header-cell>
              <mat-cell *matCellDef="let atendimento">{{atendimento.status}}</mat-cell>
            </ng-container>

            <ng-container matColumnDef="data">
              <mat-header-cell *matHeaderCellDef>Data</mat-header-cell>
              <mat-cell *matCellDef="let atendimento">{{atendimento.data | date}}</mat-cell>
            </ng-container>

            <ng-container matColumnDef="acoes">
              <mat-header-cell *matHeaderCellDef>Ações</mat-header-cell>
              <mat-cell *matCellDef="let atendimento">
                <button mat-icon-button color="primary" (click)="verChat(atendimento)">
                  <mat-icon>chat</mat-icon>
                </button>
              </mat-cell>
            </ng-container>

            <mat-header-row *matHeaderRowDef="colunas"></mat-header-row>
            <mat-row *matRowDef="let row; columns: colunas;"></mat-row>
          </mat-table>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 20px;
    }
    
    mat-card {
      margin-bottom: 20px;
    }
  `]
})
export class DashboardComponent implements OnInit {
  atendimentos = [
    { cliente: 'João Silva', status: 'Em andamento', data: new Date() },
    { cliente: 'Maria Santos', status: 'Aguardando', data: new Date() },
    { cliente: 'Pedro Oliveira', status: 'Finalizado', data: new Date() }
  ];

  colunas = ['cliente', 'status', 'data', 'acoes'];

  constructor() { }

  ngOnInit(): void {
  }

  verChat(atendimento: any): void {
    console.log('Ver chat:', atendimento);
  }
} 