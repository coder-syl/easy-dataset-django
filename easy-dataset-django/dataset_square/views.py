import json
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseServerError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Site
from .serializers import SiteSerializer


def _load_sites_from_constant():
    candidate = os.path.join(settings.BASE_DIR, "constant", "sites.json")
    if os.path.exists(candidate):
        with open(candidate, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@api_view(["GET"])
def sites_list(request):
    """
    返回站点列表：优先从数据库读取（表不空），否则回退到 constant/sites.json
    """
    try:
        qs = Site.objects.all()
        if qs.exists():
            serializer = SiteSerializer(qs, many=True)
            data = serializer.data
        else:
            data = _load_sites_from_constant()

        # 修正 image 路径：如果以 /imgs/ 开头，转换为 STATIC_URL 对应路径
        for item in data:
            if not isinstance(item, dict):
                continue
            img = item.get("image", "")
            if img and isinstance(img, str) and img.startswith("/imgs/"):
                item["image"] = settings.STATIC_URL + img.lstrip("/")
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def site_detail(request, pk):
    try:
        site = Site.objects.get(pk=pk)
        serializer = SiteSerializer(site)
        data = serializer.data
        img = data.get("image", "")
        if img and isinstance(img, str) and img.startswith("/imgs/"):
            data["image"] = settings.STATIC_URL + img.lstrip("/")
        return Response(data)
    except Site.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


