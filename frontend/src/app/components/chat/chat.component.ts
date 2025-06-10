import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    FormsModule
  ],
  template: `
    <div class="chat-container">
      <mat-card class="chat-card">
        <mat-card-header>
          <mat-card-title>Chat com João Silva</mat-card-title>
        </mat-card-header>
        
        <mat-card-content class="chat-content">
          <div class="message-list">
            <div class="message received">
              <div class="message-content">
                Olá, gostaria de agendar uma consulta.
              </div>
              <div class="message-time">10:30</div>
            </div>
            
            <div class="message sent">
              <div class="message-content">
                Olá! Claro, posso te ajudar com isso. Qual seria o melhor horário para você?
              </div>
              <div class="message-time">10:31</div>
            </div>
          </div>
        </mat-card-content>
        
        <mat-card-actions class="chat-actions">
          <mat-form-field class="message-input">
            <input matInput placeholder="Digite sua mensagem..." [(ngModel)]="novaMensagem">
          </mat-form-field>
          <button mat-icon-button color="primary" (click)="enviarMensagem()">
            <mat-icon>send</mat-icon>
          </button>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [`
    .chat-container {
      padding: 20px;
      height: calc(100vh - 104px);
      display: flex;
      flex-direction: column;
    }
    
    .chat-card {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    .chat-content {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }
    
    .message-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .message {
      max-width: 70%;
      padding: 10px;
      border-radius: 10px;
    }
    
    .message.received {
      align-self: flex-start;
      background-color: #f0f0f0;
    }
    
    .message.sent {
      align-self: flex-end;
      background-color: #e3f2fd;
    }
    
    .message-content {
      margin-bottom: 5px;
    }
    
    .message-time {
      font-size: 12px;
      color: #666;
      text-align: right;
    }
    
    .chat-actions {
      display: flex;
      gap: 10px;
      padding: 10px;
      align-items: center;
    }
    
    .message-input {
      flex: 1;
    }
  `]
})
export class ChatComponent implements OnInit {
  novaMensagem = '';

  constructor() { }

  ngOnInit(): void {
  }

  enviarMensagem(): void {
    if (this.novaMensagem.trim()) {
      console.log('Enviando mensagem:', this.novaMensagem);
      this.novaMensagem = '';
    }
  }
} 