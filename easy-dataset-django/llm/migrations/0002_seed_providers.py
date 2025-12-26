from django.db import migrations


def seed_providers(apps, schema_editor):
    LlmProvider = apps.get_model('llm', 'LlmProvider')
    providers = [
        {'id': 'ollama', 'name': 'Ollama', 'api_url': 'http://127.0.0.1:11434/api'},
        {'id': 'openai', 'name': 'OpenAI', 'api_url': 'https://api.openai.com/v1/'},
        {'id': 'zhipu', 'name': '智谱AI', 'api_url': 'https://open.bigmodel.cn/api/paas/v4/'},
        {'id': 'openrouter', 'name': 'OpenRouter', 'api_url': 'https://openrouter.ai/api/v1/'},
        {'id': 'siliconcloud', 'name': '硅基流动', 'api_url': 'https://api.siliconflow.cn/v1/'},
        {'id': 'deepseek', 'name': 'DeepSeek', 'api_url': 'https://api.deepseek.com/v1/'},
        {'id': '302ai', 'name': '302.AI', 'api_url': 'https://api.302.ai/v1/'},
        {'id': 'Doubao', 'name': '火山引擎', 'api_url': 'https://ark.cn-beijing.volces.com/api/v3/'},
        {'id': 'groq', 'name': 'Groq', 'api_url': 'https://api.groq.com/openai'},
        {'id': 'grok', 'name': 'Grok', 'api_url': 'https://api.x.ai/v1'},
        {'id': 'alibailian', 'name': '阿里云百炼', 'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'},
    ]

    for p in providers:
        LlmProvider.objects.update_or_create(id=p['id'], defaults={'name': p['name'], 'api_url': p['api_url']})


def remove_providers(apps, schema_editor):
    LlmProvider = apps.get_model('llm', 'LlmProvider')
    ids = ['ollama', 'openai', 'zhipu', 'openrouter', 'siliconcloud', 'deepseek', '302ai', 'Doubao', 'groq', 'grok', 'alibailian']
    LlmProvider.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_providers, remove_providers),
    ]


