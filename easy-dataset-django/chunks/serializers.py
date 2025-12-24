"""
文本块序列化器
"""
from rest_framework import serializers
from .models import Chunk


class ChunkSerializer(serializers.ModelSerializer):
    """文本块序列化器"""
    
    class Meta:
        model = Chunk
        fields = [
            'id', 'name', 'file_id', 'file_name', 'content', 'summary', 'size',
            'create_at', 'update_at'
        ]
        read_only_fields = ['id', 'create_at', 'update_at']
    
    def update(self, instance, validated_data):
        """
        当 content 被更新时，自动更新 size 为 content 的字符长度。
        这样可以保证通过 PUT/PATCH 更新 content 后，数据库中的 size 字段始终正确。
        """
        # If content provided, compute size and include in validated_data so super().update persists it.
        if 'content' in validated_data and validated_data['content'] is not None:
            try:
                validated_data['size'] = len(validated_data['content'])
            except Exception:
                # fallback: do not set size if something unexpected
                pass

        # Delegate to default implementation to perform update and save
        instance = super().update(instance, validated_data)

        # As an extra safety, ensure instance.size matches content length
        try:
            if instance.content is not None:
                computed = len(instance.content)
                if instance.size != computed:
                    instance.size = computed
                    instance.save(update_fields=['size'])
        except Exception:
            # ignore failures to avoid blocking update
            pass

        return instance

