# beautyshop_blog/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Post

def post_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش لیست مقالات.
    چون تعداد لایک‌ها در مدل کش شده است، کوئری بسیار سریع اجرا می‌شود.
    """
    posts = Post.objects.filter(is_published=True).select_related(
        'author', 'category'
    ).order_by('-created_at')
    
    return render(request, 'beautyshop_blog/post_list.html', {'posts': posts})

def post_detail_view(request: HttpRequest, slug: str) -> HttpResponse:
    """
    نمایش جزئیات مقاله.
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        slug=slug, 
        is_published=True
    )
    
    # افزایش بازدید (Atomic)
    post.view_count = F('view_count') + 1
    post.save(update_fields=['view_count'])
    post.refresh_from_db()
    
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(id=request.user.id).exists()
    
    return render(request, 'beautyshop_blog/post_detail.html', {
        'post': post,
        'is_liked': is_liked 
    })

@login_required
@require_POST
def like_toggle_view(request: HttpRequest, pk: int) -> JsonResponse:
    """
    API لایک/آنلایک.
    سیگنال‌ها (در models.py) مسئولیت آپدیت کردن عدد لایک را بر عهده دارند.
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
        
        # برای اطمینان از خواندن مقدار جدید (که توسط سیگنال آپدیت شده)
        # می‌توانیم رفرش کنیم، اما چون سیگنال همزمان اجرا می‌شود، دسترسی مستقیم هم امن است
        post.refresh_from_db()
            
        return JsonResponse({
            'status': 'success', 
            'liked': liked, 
            'count': post.total_likes # خواندن از پراپرتی سریع
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)