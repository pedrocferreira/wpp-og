import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ToastService, Toast } from '../../services/toast.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  template: `
    <div class="toast-container">
      <div 
        *ngFor="let toast of toasts; trackBy: trackByToastId" 
        class="toast"
        [ngClass]="toast.type"
        [@slideIn]>
        
        <div class="toast-content">
          <div class="toast-icon">
            <mat-icon>{{ getIcon(toast.type) }}</mat-icon>
          </div>
          
          <div class="toast-text">
            <div class="toast-title">{{ toast.title }}</div>
            <div class="toast-message" *ngIf="toast.message">{{ toast.message }}</div>
          </div>
          
          <div class="toast-actions">
            <button 
              *ngIf="toast.action"
              mat-button
              (click)="executeAction(toast)"
              class="toast-action-btn">
              {{ toast.action.label }}
            </button>
            
            <button 
              mat-icon-button
              (click)="removeToast(toast.id)"
              class="toast-close-btn">
              <mat-icon>close</mat-icon>
            </button>
          </div>
        </div>
        
        <div class="toast-progress" *ngIf="toast.duration">
          <div class="toast-progress-bar" [style.animation-duration]="toast.duration + 'ms'"></div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .toast-container {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      max-width: 420px;
      pointer-events: none;
    }

    .toast {
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
      margin-bottom: 12px;
      overflow: hidden;
      border-left: 4px solid;
      pointer-events: auto;
      animation: slideInRight 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      position: relative;
    }

    .toast.success {
      border-left-color: #10b981;
    }

    .toast.error {
      border-left-color: #ef4444;
    }

    .toast.warning {
      border-left-color: #f59e0b;
    }

    .toast.info {
      border-left-color: #8B5CF6;
    }

    .toast-content {
      display: flex;
      align-items: flex-start;
      padding: 16px;
      gap: 12px;
    }

    .toast-icon {
      flex-shrink: 0;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }

    .toast.success .toast-icon {
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
    }

    .toast.error .toast-icon {
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
    }

    .toast.warning .toast-icon {
      background: rgba(245, 158, 11, 0.1);
      color: #f59e0b;
    }

    .toast.info .toast-icon {
      background: rgba(139, 92, 246, 0.1);
      color: #8B5CF6;
    }

    .toast-icon mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    .toast-text {
      flex: 1;
      min-width: 0;
    }

    .toast-title {
      font-weight: 600;
      font-size: 14px;
      color: #1f2937;
      margin-bottom: 2px;
      line-height: 1.4;
    }

    .toast-message {
      font-size: 13px;
      color: #6b7280;
      line-height: 1.4;
    }

    .toast-actions {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
    }

    .toast-action-btn {
      min-width: auto !important;
      padding: 4px 12px !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      height: 32px !important;
    }

    .toast.success .toast-action-btn {
      color: #10b981 !important;
    }

    .toast.error .toast-action-btn {
      color: #ef4444 !important;
    }

    .toast.warning .toast-action-btn {
      color: #f59e0b !important;
    }

    .toast.info .toast-action-btn {
      color: #8B5CF6 !important;
    }

    .toast-close-btn {
      width: 32px !important;
      height: 32px !important;
      color: #9ca3af !important;
    }

    .toast-close-btn:hover {
      color: #6b7280 !important;
      background: rgba(0, 0, 0, 0.05) !important;
    }

    .toast-close-btn mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
    }

    .toast-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(0, 0, 0, 0.05);
      overflow: hidden;
    }

    .toast-progress-bar {
      height: 100%;
      width: 100%;
      transform-origin: left;
      animation: toastProgress linear forwards;
    }

    .toast.success .toast-progress-bar {
      background: #10b981;
    }

    .toast.error .toast-progress-bar {
      background: #ef4444;
    }

    .toast.warning .toast-progress-bar {
      background: #f59e0b;
    }

    .toast.info .toast-progress-bar {
      background: #8B5CF6;
    }

    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes toastProgress {
      from {
        transform: scaleX(1);
      }
      to {
        transform: scaleX(0);
      }
    }

    @media (max-width: 768px) {
      .toast-container {
        top: 10px;
        right: 10px;
        left: 10px;
        max-width: none;
      }

      .toast-content {
        padding: 12px;
      }

      .toast-title {
        font-size: 13px;
      }

      .toast-message {
        font-size: 12px;
      }
    }
  `],
  animations: [
    // Adicionar animações do Angular aqui se necessário
  ]
})
export class ToastComponent implements OnInit, OnDestroy {
  toasts: Toast[] = [];
  private subscription!: Subscription;

  constructor(private toastService: ToastService) {}

  ngOnInit(): void {
    this.subscription = this.toastService.toasts$.subscribe(toasts => {
      this.toasts = toasts;
    });
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  trackByToastId(index: number, toast: Toast): string {
    return toast.id;
  }

  getIcon(type: string): string {
    switch (type) {
      case 'success':
        return 'check_circle';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'info';
    }
  }

  removeToast(id: string): void {
    this.toastService.remove(id);
  }

  executeAction(toast: Toast): void {
    if (toast.action) {
      toast.action.callback();
      this.removeToast(toast.id);
    }
  }
} 