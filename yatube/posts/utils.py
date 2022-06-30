from django.core.paginator import Paginator
from django.conf import settings


def paginate_page(request, posts):
    paginator = Paginator(posts, settings.COUNT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
