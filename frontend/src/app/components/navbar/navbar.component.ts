import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [
    CommonModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule
  ],
  template: `
    <mat-toolbar color="primary" class="navbar">
      <div class="navbar-content">
        <div class="navbar-brand">
          <div class="logo-container hover-scale">
            <img src="logo.png" alt="Logo" class="brand-logo" (load)="onLogoLoad()" (error)="onLogoError()">
            <mat-icon class="brand-icon-fallback" [style.display]="showFallback ? 'flex' : 'none'">psychology</mat-icon>
          </div>
          <div class="brand-text">
            <span class="brand-title">Sistema Inteligente</span>
            <span class="brand-subtitle">Gestão & Atendimento</span>
          </div>
        </div>
        
        <div class="navbar-user" *ngIf="authService.currentUser$ | async as user">
          <span class="user-greeting">Olá, {{user.first_name || user.username}}!</span>
          
          <button mat-icon-button [matMenuTriggerFor]="userMenu" class="user-menu-btn pulse-on-hover">
            <mat-icon>account_circle</mat-icon>
          </button>
          
          <mat-menu #userMenu="matMenu" class="user-menu">
            <div class="user-info">
              <div class="user-avatar">
                <mat-icon>person</mat-icon>
              </div>
              <div class="user-details">
                <div class="user-name">{{user.first_name}} {{user.last_name}}</div>
                <div class="user-email">{{user.email}}</div>
                <div class="user-role">{{getRoleLabel(user.role)}}</div>
              </div>
            </div>
            <mat-divider></mat-divider>
            <button mat-menu-item (click)="logout()" class="logout-btn">
              <mat-icon>logout</mat-icon>
              <span>Sair do Sistema</span>
            </button>
          </mat-menu>
        </div>
      </div>
    </mat-toolbar>
  `,
  styles: [`
    .navbar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 1000;
      background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 50%, #7C3AED 100%);
      box-shadow: 0 4px 32px rgba(139, 92, 246, 0.3);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      transition: all 0.3s ease;
      
      &:hover {
        box-shadow: 0 6px 40px rgba(139, 92, 246, 0.4);
      }
      
      .navbar-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        padding: 0 16px;
        
        .navbar-brand {
          display: flex;
          align-items: center;
          gap: 16px;
          transition: transform 0.3s ease;
          
          &:hover {
            transform: scale(1.02);
          }
          
          .logo-container {
            position: relative;
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            
            &:hover {
              background: rgba(255, 255, 255, 0.2);
              transform: rotate(5deg);
            }
            
            .brand-logo {
              width: 40px;
              height: 40px;
              object-fit: contain;
              border-radius: 8px;
              filter: brightness(1.1) contrast(1.1);
              z-index: 2;
              position: relative;
            }
            
            .brand-icon-fallback {
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 32px;
              height: 32px;
              font-size: 28px;
              color: rgba(255, 255, 255, 0.9);
              display: flex;
              align-items: center;
              justify-content: center;
              z-index: 1;
            }
          }
          
          .brand-text {
            display: flex;
            flex-direction: column;
            
            .brand-title {
              font-size: 22px;
              font-weight: 700;
              color: white;
              line-height: 1.2;
              letter-spacing: -0.5px;
              text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            
            .brand-subtitle {
              font-size: 11px;
              color: rgba(255, 255, 255, 0.85);
              font-weight: 500;
              letter-spacing: 0.8px;
              text-transform: uppercase;
              opacity: 0.9;
            }
          }
        }
        
        .navbar-user {
          display: flex;
          align-items: center;
          gap: 20px;
          
          .user-greeting {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.95);
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }
          
          .user-menu-btn {
            width: 48px;
            height: 48px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 50%;
            transition: all 0.3s ease;
            border: 2px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(8px);
            
            &:hover {
              background: rgba(255, 255, 255, 0.25);
              transform: scale(1.1);
              border-color: rgba(255, 255, 255, 0.4);
              box-shadow: 0 4px 16px rgba(255, 255, 255, 0.3);
            }
            
            mat-icon {
              font-size: 26px;
              color: white;
              text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
          }
        }
      }
    }
    
    .user-menu {
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3);
      border: 1px solid rgba(139, 92, 246, 0.2);
      backdrop-filter: blur(16px);
      
      .user-info {
        padding: 20px;
        display: flex;
        gap: 16px;
        align-items: center;
        background: linear-gradient(135deg, #faf9ff 0%, #f3f1ff 100%);
        border-bottom: 1px solid rgba(139, 92, 246, 0.1);
        
        .user-avatar {
          width: 56px;
          height: 56px;
          background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
          border: 3px solid rgba(255, 255, 255, 0.8);
          
          mat-icon {
            color: white;
            font-size: 28px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
          }
        }
        
        .user-details {
          .user-name {
            font-weight: 700;
            font-size: 15px;
            color: #2d1b69;
            margin-bottom: 4px;
            letter-spacing: -0.2px;
          }
          
          .user-email {
            font-size: 12px;
            color: #6b46c1;
            margin-bottom: 6px;
            opacity: 0.8;
          }
          
          .user-role {
            font-size: 10px;
            color: #8B5CF6;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            background: rgba(139, 92, 246, 0.1);
            padding: 2px 8px;
            border-radius: 12px;
            display: inline-block;
          }
        }
      }
      
      .logout-btn {
        color: #dc2626;
        font-weight: 600;
        padding: 12px 20px;
        transition: all 0.3s ease;
        
        mat-icon {
          color: #dc2626;
          margin-right: 8px;
        }
        
        &:hover {
          background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%);
          color: #b91c1c;
          
          mat-icon {
            color: #b91c1c;
          }
        }
      }
    }
    
    @media (max-width: 768px) {
      .navbar-content {
        padding: 0 12px;
        
        .navbar-brand {
          gap: 12px;
          
          .logo-container {
            width: 40px;
            height: 40px;
            
            .brand-logo {
              width: 32px;
              height: 32px;
            }
            
            .brand-icon-fallback {
              width: 28px;
              height: 28px;
              font-size: 22px;
            }
          }
          
          .brand-text {
            .brand-title {
              font-size: 18px;
            }
            
            .brand-subtitle {
              font-size: 10px;
            }
          }
        }
        
        .navbar-user {
          gap: 12px;
          
          .user-greeting {
            display: none;
          }
          
          .user-menu-btn {
            width: 40px;
            height: 40px;
            
            mat-icon {
              font-size: 22px;
            }
          }
        }
      }
    }
    
    @media (max-width: 480px) {
      .navbar-content {
        padding: 0 8px;
        
        .navbar-brand {
          .brand-text {
            .brand-title {
              font-size: 16px;
            }
          }
        }
      }
    }
  `]
})
export class NavbarComponent implements OnInit {
  showFallback = true; // Inicialmente mostra o fallback até o logo carregar

  constructor(
    public authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {}

  logout(): void {
    this.authService.logout();
  }

  getRoleLabel(role: string): string {
    const labels: { [key: string]: string } = {
      'admin': 'Administrador',
      'attendant': 'Atendente'
    };
    return labels[role] || role;
  }

  onLogoLoad(): void {
    this.showFallback = false;
  }

  onLogoError(): void {
    this.showFallback = true;
  }
} 