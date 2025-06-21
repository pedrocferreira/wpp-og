import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
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
    MatTooltipModule,
    FormsModule
  ],
  template: `
    <div class="chat-container">
      <!-- Header da conversa -->
      <div class="chat-header">
        <div class="contact-info">
          <div class="contact-avatar">
            <mat-icon>account_circle</mat-icon>
          </div>
          <div class="contact-details">
            <h3>João Silva</h3>
            <span class="contact-status">Online agora</span>
          </div>
        </div>
        <div class="chat-actions-header">
          <button mat-icon-button matTooltip="Informações do cliente">
            <mat-icon>info</mat-icon>
          </button>
          <button mat-icon-button matTooltip="Histórico">
            <mat-icon>history</mat-icon>
          </button>
        </div>
      </div>

      <!-- Área de mensagens -->
      <div class="messages-area">
        <div class="message-list">
          <div class="message received">
            <div class="message-bubble">
              <div class="message-content">
                Olá, gostaria de agendar uma consulta.
              </div>
              <div class="message-time">10:30</div>
            </div>
          </div>
          
          <div class="message sent">
            <div class="message-bubble">
              <div class="message-content">
                Olá! Claro, posso te ajudar com isso. Qual seria o melhor horário para você?
              </div>
              <div class="message-time">10:31</div>
            </div>
          </div>

          <div class="message received">
            <div class="message-bubble">
              <div class="message-content">
                Preferencialmente pela manhã, entre 8h e 11h.
              </div>
              <div class="message-time">10:32</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Área de entrada de mensagem -->
      <div class="message-input-area">
        <div class="input-container">
          <mat-form-field class="message-field" appearance="outline">
            <input matInput 
                   placeholder="Digite sua mensagem..." 
                   [(ngModel)]="novaMensagem"
                   (keydown.enter)="enviarMensagem()">
          </mat-form-field>
          <button mat-fab 
                  color="primary" 
                  class="send-button"
                  (click)="enviarMensagem()"
                  [disabled]="!novaMensagem.trim()">
            <mat-icon>send</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chat-container {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 70px);
      background: white;
      border-radius: 12px;
      margin: 24px;
      box-shadow: 0 4px 20px rgba(107, 70, 193, 0.1);
      overflow: hidden;
    }

    /* Header do chat */
    .chat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 24px;
      background: linear-gradient(135deg, #6b46c1, #8b5cf6);
      color: white;
      border-bottom: 1px solid #e2e8f0;
    }

    .contact-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .contact-avatar mat-icon {
      font-size: 40px;
      width: 40px;
      height: 40px;
      color: rgba(255, 255, 255, 0.9);
    }

    .contact-details h3 {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .contact-status {
      font-size: 0.85rem;
      opacity: 0.8;
    }

    .chat-actions-header {
      display: flex;
      gap: 8px;
    }

    .chat-actions-header button {
      color: rgba(255, 255, 255, 0.9);
    }

    .chat-actions-header button:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    /* Área de mensagens */
    .messages-area {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      background: #f8fafc;
    }

    .message-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      display: flex;
      max-width: 70%;
    }

    .message.received {
      align-self: flex-start;
    }

    .message.sent {
      align-self: flex-end;
    }

    .message-bubble {
      padding: 12px 16px;
      border-radius: 18px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .message.received .message-bubble {
      background: white;
      border-bottom-left-radius: 6px;
    }

    .message.sent .message-bubble {
      background: linear-gradient(135deg, #6b46c1, #8b5cf6);
      color: white;
      border-bottom-right-radius: 6px;
    }

    .message-content {
      margin-bottom: 6px;
      line-height: 1.4;
      word-wrap: break-word;
    }

    .message-time {
      font-size: 0.75rem;
      opacity: 0.7;
      text-align: right;
    }

    .message.received .message-time {
      color: #64748b;
    }

    .message.sent .message-time {
      color: rgba(255, 255, 255, 0.8);
    }

    /* Área de entrada de mensagem */
    .message-input-area {
      padding: 16px 24px;
      background: white;
      border-top: 1px solid #e2e8f0;
    }

    .input-container {
      display: flex;
      align-items: flex-end;
      gap: 12px;
    }

    .message-field {
      flex: 1;
    }

    .message-field ::ng-deep .mat-mdc-form-field-wrapper {
      padding-bottom: 0;
    }

    .send-button {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #6b46c1, #8b5cf6);
    }

    .send-button:disabled {
      background: #e2e8f0;
      color: #94a3b8;
    }

    .send-button mat-icon {
      font-size: 20px;
      width: 20px;
      height: 20px;
    }

    /* Responsividade */
    @media (max-width: 768px) {
      .chat-container {
        margin: 16px;
        height: calc(100vh - 102px);
      }

      .chat-header {
        padding: 12px 16px;
      }

      .contact-details h3 {
        font-size: 1rem;
      }

      .contact-status {
        font-size: 0.8rem;
      }

      .messages-area {
        padding: 16px;
      }

      .message {
        max-width: 85%;
      }

      .message-input-area {
        padding: 12px 16px;
      }

      .send-button {
        width: 44px;
        height: 44px;
      }
    }

    /* Scrollbar customizada */
    .messages-area::-webkit-scrollbar {
      width: 6px;
    }

    .messages-area::-webkit-scrollbar-track {
      background: #f1f5f9;
    }

    .messages-area::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;
    }

    .messages-area::-webkit-scrollbar-thumb:hover {
      background: #94a3b8;
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