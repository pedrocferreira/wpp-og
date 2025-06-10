from rest_framework import serializers
from .models import WhatsAppMessage, AIResponse
from appointments.serializers import ClientSerializer

class WhatsAppMessageSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'client', 'client_id', 'message_type',
            'content', 'media_url', 'media_type',
            'timestamp', 'status', 'processed_by_ai'
        ]

class AIResponseSerializer(serializers.ModelSerializer):
    processed_by = serializers.SerializerMethodField()

    class Meta:
        model = AIResponse
        fields = [
            'id', 'message', 'response_text',
            'confidence_score', 'intent_detected',
            'created_at', 'processed_by'
        ]

    def get_processed_by(self, obj):
        if obj.processed_by:
            return {
                'id': obj.processed_by.id,
                'username': obj.processed_by.username
            }
        return None 