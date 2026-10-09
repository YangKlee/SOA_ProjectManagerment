from rest_framework import serializers
class TopicRequestDTO(serializers.Serializer):
    topic_id=serializers.CharField(max_length=255)
    name=serializers.CharField()
    description=serializers.CharField(required=False,allow_null=True,allow_blank=True)
    file_url=serializers.CharField(required=False,allow_null=True,allow_blank=True)
    major_id=serializers.CharField()
    status=serializers.IntegerField(required=False,allow_null=True)
    advisor_id=serializers.CharField(required=False,allow_null=True,allow_blank=True)
class TopicResponseDTO(TopicRequestDTO): pass
