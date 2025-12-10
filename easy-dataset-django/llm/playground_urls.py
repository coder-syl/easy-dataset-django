"""
LLM Playground URL配置
"""
from django.urls import path
from . import playground_views

app_name = 'llm_playground'

urlpatterns = [
    path('chat/', playground_views.playground_chat, name='chat'),  # POST: 聊天
    path('chat/stream/', playground_views.playground_chat_stream, name='chat_stream'),  # POST: 流式聊天
]

