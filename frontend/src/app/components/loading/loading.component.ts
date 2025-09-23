import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-loading',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule],
  template: `
    <div class="loading-container" [ngClass]="'loading-' + type">
      
      <!-- Skeleton Loading -->
      <div *ngIf="type === 'skeleton'" class="skeleton-container">
        <div class="skeleton skeleton-title" *ngIf="showTitle"></div>
        <div class="skeleton skeleton-text" *ngFor="let line of skeletonLines"></div>
        <div class="skeleton skeleton-card" *ngIf="showCard"></div>
      </div>

      <!-- Spinner Loading -->
      <div *ngIf="type === 'spinner'" class="spinner-container">
        <div class="loading-spinner" [style.width.px]="size" [style.height.px]="size">
          <div class="spinner-inner"></div>
        </div>
        <p *ngIf="message" class="loading-message">{{ message }}</p>
      </div>

      <!-- Dots Loading -->
      <div *ngIf="type === 'dots'" class="dots-container">
        <div class="dots-spinner">
          <div class="dot dot1"></div>
          <div class="dot dot2"></div>
          <div class="dot dot3"></div>
        </div>
        <p *ngIf="message" class="loading-message">{{ message }}</p>
      </div>

      <!-- Pulse Loading -->
      <div *ngIf="type === 'pulse'" class="pulse-container">
        <div class="pulse-spinner">
          <div class="pulse-ring pulse-ring-1"></div>
          <div class="pulse-ring pulse-ring-2"></div>
          <div class="pulse-ring pulse-ring-3"></div>
        </div>
        <p *ngIf="message" class="loading-message">{{ message }}</p>
      </div>

      <!-- Overlay Loading -->
      <div *ngIf="type === 'overlay'" class="overlay-container">
        <div class="overlay-backdrop"></div>
        <div class="overlay-content">
          <div class="loading-spinner">
            <div class="spinner-inner"></div>
          </div>
          <p *ngIf="message" class="loading-message">{{ message }}</p>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .loading-container {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    /* Skeleton Loading */
    .skeleton-container {
      width: 100%;
      max-width: 400px;
    }

    .skeleton {
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.8s infinite;
      border-radius: 8px;
    }

    .skeleton-title {
      height: 24px;
      width: 60%;
      margin-bottom: 16px;
    }

    .skeleton-text {
      height: 16px;
      margin-bottom: 8px;
    }

    .skeleton-text:nth-child(2) { width: 100%; }
    .skeleton-text:nth-child(3) { width: 85%; }
    .skeleton-text:nth-child(4) { width: 70%; }

    .skeleton-card {
      height: 120px;
      margin-top: 16px;
    }

    @keyframes skeleton-loading {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }

    /* Spinner Loading */
    .spinner-container {
      text-align: center;
    }

    .loading-spinner {
      position: relative;
      margin: 0 auto 16px;
    }

    .spinner-inner {
      width: 100%;
      height: 100%;
      border: 3px solid var(--purple-200, #e5e7eb);
      border-top: 3px solid var(--primary-purple, #8B5CF6);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Dots Loading */
    .dots-container {
      text-align: center;
    }

    .dots-spinner {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }

    .dot {
      width: 12px;
      height: 12px;
      background: var(--primary-purple, #8B5CF6);
      border-radius: 50%;
      animation: dotPulse 1.4s ease-in-out infinite both;
    }

    .dot1 { animation-delay: 0s; }
    .dot2 { animation-delay: 0.2s; }
    .dot3 { animation-delay: 0.4s; }

    @keyframes dotPulse {
      0%, 80%, 100% {
        transform: scale(0.5);
        opacity: 0.5;
      }
      40% {
        transform: scale(1);
        opacity: 1;
      }
    }

    /* Pulse Loading */
    .pulse-container {
      text-align: center;
    }

    .pulse-spinner {
      position: relative;
      width: 60px;
      height: 60px;
      margin: 0 auto 16px;
    }

    .pulse-ring {
      position: absolute;
      border: 2px solid var(--primary-purple, #8B5CF6);
      border-radius: 50%;
      animation: pulseRing 2s linear infinite;
    }

    .pulse-ring-1 {
      width: 20px;
      height: 20px;
      top: 20px;
      left: 20px;
    }

    .pulse-ring-2 {
      width: 40px;
      height: 40px;
      top: 10px;
      left: 10px;
      animation-delay: 0.5s;
    }

    .pulse-ring-3 {
      width: 60px;
      height: 60px;
      top: 0;
      left: 0;
      animation-delay: 1s;
    }

    @keyframes pulseRing {
      0% {
        transform: scale(0.8);
        opacity: 1;
      }
      100% {
        transform: scale(1.2);
        opacity: 0;
      }
    }

    /* Overlay Loading */
    .overlay-container {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 9999;
    }

    .overlay-backdrop {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
    }

    .overlay-content {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      background: white;
      padding: 40px;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(139, 92, 246, 0.2);
      border: 1px solid rgba(139, 92, 246, 0.1);
    }

    /* Loading Message */
    .loading-message {
      color: var(--gray-600, #6b7280);
      font-size: 14px;
      font-weight: 500;
      margin: 0;
      animation: fadeInOut 2s ease-in-out infinite;
    }

    @keyframes fadeInOut {
      0%, 100% { opacity: 0.6; }
      50% { opacity: 1; }
    }

    /* Responsive */
    @media (max-width: 768px) {
      .overlay-content {
        margin: 20px;
        padding: 32px 24px;
      }

      .loading-message {
        font-size: 13px;
      }
    }
  `]
})
export class LoadingComponent {
  @Input() type: 'skeleton' | 'spinner' | 'dots' | 'pulse' | 'overlay' = 'spinner';
  @Input() size: number = 40;
  @Input() message: string = '';
  @Input() showTitle: boolean = true;
  @Input() showCard: boolean = false;
  @Input() skeletonLines: number[] = [1, 2, 3];
} 