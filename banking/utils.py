from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.db.models import Q


def smart_table_response(request, queryset, *, search_fields, filter_fields, serialize, default_sort="-date"):
    """
    Applies the same search / filter / sort / paginate contract every smart
    table on the frontend expects (see static/js/app.js `mountSmartTable`,
    which now calls the API instead of filtering an in-memory array):

      ?search=text        → icontains across `search_fields`
      ?status=pending      → exact match, one entry per name in `filter_fields`
      ?sort=amount&dir=asc → order_by, falls back to `default_sort`
      ?page=2&page_size=8

    Returns a plain dict ready for JsonResponse: {results, total, page, pages}.
    """
    search = request.GET.get("search", "").strip()
    if search and search_fields:
        q = Q()
        for f in search_fields:
            q |= Q(**{f"{f}__icontains": search})
        queryset = queryset.filter(q)

    for field in filter_fields:
        value = request.GET.get(field)
        if value and value != "all":
            queryset = queryset.filter(**{field: value})

    sort_key = request.GET.get("sort")
    sort_dir = request.GET.get("dir", "asc")
    if sort_key:
        ordering = sort_key if sort_dir == "asc" else f"-{sort_key}"
        try:
            # .ordered forces evaluation of the ORDER BY clause's field
            # names right away, so a bogus ?sort= from a hand-crafted
            # request can't blow up later with an uncaught FieldError.
            queryset = queryset.order_by(ordering)
            str(queryset.query)
        except FieldError:
            queryset = queryset.order_by(default_sort)
    else:
        queryset = queryset.order_by(default_sort)

    page_size = min(int(request.GET.get("page_size", 8) or 8), 100)
    page_number = int(request.GET.get("page", 1) or 1)
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(page_number)

    return {
        "results": [serialize(obj) for obj in page.object_list],
        "total": paginator.count,
        "page": page.number,
        "pages": paginator.num_pages,
    }
