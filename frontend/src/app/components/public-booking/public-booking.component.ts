import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ApiService } from '../../services/api.service'; // Ajuste o caminho se necessário
import { ActivatedRoute } from '@angular/router';

// Angular Material Imports
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

@Component({
  selector: 'app-public-booking',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    // HttpClientModule não é mais necessário aqui pois é provido globalmente
    // Angular Material
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule
  ],
  templateUrl: './public-booking.component.html',
  styleUrls: ['./public-booking.component.scss']
})
export class PublicBookingComponent implements OnInit {
  bookingForm: FormGroup;
  availableSlots: string[] = [];
  selectedDate: string = '';
  isLoading = false;
  bookingSuccess = false;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private route: ActivatedRoute
  ) {
    this.bookingForm = this.fb.group({
      name: ['', Validators.required],
      whatsapp: ['', [Validators.required, Validators.pattern('^[0-9]{10,15}$')]],
      date: ['', Validators.required],
      time: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const whatsapp = params['whatsapp'];
      if (whatsapp) {
        this.bookingForm.patchValue({ whatsapp });
      }
    });
  }

  onDateChange(event: any): void {
    const selectedDate = event.value as Date;
    this.selectedDate = selectedDate.toISOString().split('T')[0];
    this.bookingForm.patchValue({ date: this.selectedDate, time: '' });
    this.availableSlots = [];
    this.errorMessage = '';

    if (this.selectedDate) {
      this.isLoading = true;
      this.apiService.getAvailableTimeSlots(new Date(this.selectedDate), 'online').subscribe({
        next: (slots: string[]) => {
          this.availableSlots = slots;
          this.isLoading = false;
        },
        error: (err: any) => {
          console.error('Erro ao buscar horários:', err);
          this.errorMessage = 'Não foi possível carregar os horários. Tente outra data.';
          this.isLoading = false;
        }
      });
    }
  }

  selectTime(time: string): void {
    this.bookingForm.patchValue({ time });
  }

  onSubmit(): void {
    if (this.bookingForm.invalid) {
      this.errorMessage = 'Por favor, preencha todos os campos corretamente.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.bookingSuccess = false;

    const formData = {
      client_name: this.bookingForm.value.name,
      client_whatsapp: this.bookingForm.value.whatsapp,
      consultation_type: 'online', // Pode ser dinâmico se necessário
      date: this.bookingForm.value.date,
      time: this.bookingForm.value.time
    };

    this.apiService.createAppointment(formData).subscribe({
      next: (response: any) => {
        this.isLoading = false;
        this.bookingSuccess = true;
        console.log('Agendamento realizado:', response);
      },
      error: (err: any) => {
        console.error('Erro ao agendar:', err);
        this.errorMessage = err.error?.error || 'Ocorreu um erro ao realizar o agendamento. Por favor, tente novamente.';
        this.isLoading = false;
      }
    });
  }
}
