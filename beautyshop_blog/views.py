# beautyshop_blog/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import F, Q
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Post, Category

def post_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش لیست مقالات با قابلیت جستجو و صفحه‌بندی.
    """
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category')
    
    # کوئری پایه با بهینه‌سازی
    posts = Post.objects.filter(is_published=True).select_related(
        'author', 'category'
    ).order_by('-created_at')
    
    # فیلتر جستجو
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(meta_description__icontains=query)
        )
    
    # فیلتر دسته‌بندی
    current_category = None
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
        current_category = Category.objects.filter(slug=category_slug).first()

    # صفحه‌بندی (۹ پست در هر صفحه)
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # دریافت دسته‌بندی‌ها برای سایدبار یا فیلتر
    categories = Category.objects.all()
    
    # پست ویژه (آخرین پست) برای نمایش بزرگتر در صفحه اول (اگر جستجو نباشد)
    featured_post = None
    if not query and not category_slug and page_obj.number == 1 and len(posts) > 0:
        featured_post = page_obj[0]
        # حذف پست ویژه از لیست عادی صفحه اول تا تکراری نشود
        # نکته: چون page_obj یک QuerySet اسلایس شده است، نمی‌توانیم pop کنیم.
        # در تمپلیت هندل می‌کنیم (slice:1 را جدا می‌کنیم)

    context = {
        'posts': page_obj,
        'featured_post': featured_post,
        'query': query,
        'categories': categories,
        'current_category': current_category
    }
    return render(request, 'beautyshop_blog/post_list.html', context)

def post_detail_view(request: HttpRequest, slug: str) -> HttpResponse:
    """
    نمایش جزئیات مقاله به همراه پیشنهادات مرتبط.
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'related_service'),
        slug=slug, 
        is_published=True
    )
    
    # افزایش بازدید
    post.view_count = F('view_count') + 1
    post.save(update_fields=['view_count'])
    post.refresh_from_db()
    
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(id=request.user.id).exists()
        
    # یافتن مقالات مرتبط (از همین دسته، به جز خود مقاله)
    related_posts = Post.objects.filter(
        is_published=True, 
        category=post.category
    ).exclude(id=post.id).order_by('-created_at')[:3]
    
    return render(request, 'beautyshop_blog/post_detail.html', {
        'post': post,
        'is_liked': is_liked,
        'related_posts': related_posts
    })

@login_required
@require_POST
def like_toggle_view(request: HttpRequest, pk: int) -> JsonResponse:
    """
    API لایک/آنلایک.
    """
    try:
        post = get_object_or_404(Post, id=pk)
        user = request.user
        
        if post.likes.filter(id=user.id).exists():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True
        
        post.refresh_from_db()
            
        return JsonResponse({
            'status': 'success', 
            'liked': liked, 
            'count': post.total_likes
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)