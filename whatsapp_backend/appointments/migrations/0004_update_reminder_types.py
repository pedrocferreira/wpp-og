# Generated manually to update reminder types

from django.db import migrations

def update_reminder_types(apps, schema_editor):
    """Atualiza tipos de lembrete existentes"""
    AppointmentReminder = apps.get_model('appointments', 'AppointmentReminder')
    
    # Atualiza todos os lembretes de '1_hour' para '2_hours'
    AppointmentReminder.objects.filter(reminder_type='1_hour').update(reminder_type='2_hours')
    
    # Remove lembretes do tipo '2_days' se existirem
    AppointmentReminder.objects.filter(reminder_type='2_days').delete()
    
    print("Tipos de lembrete atualizados com sucesso!")

def reverse_update_reminder_types(apps, schema_editor):
    """Reverte os tipos de lembrete"""
    AppointmentReminder = apps.get_model('appointments', 'AppointmentReminder')
    
    # Reverte de '2_hours' para '1_hour'
    AppointmentReminder.objects.filter(reminder_type='2_hours').update(reminder_type='1_hour')

class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_appointmentreminder_alter_appointment_options_and_more'),
    ]

    operations = [
        migrations.RunPython(update_reminder_types, reverse_update_reminder_types),
    ] 