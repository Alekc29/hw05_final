from django.core.paginator import Paginator


def paginator(request, post, per_page: int):
    ''' Пагинатор выводит на одну страницу PER_PAGE постов. '''
    pt = Paginator(post, per_page)
    page_number = request.GET.get('page')
    return pt.get_page(page_number)
