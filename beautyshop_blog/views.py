# beautyshop_blog/views.py
"""
ویوهای مربوط به اپلیکیشن وبلاگ (beautyshop_blog).
"""

from django.shortcuts import render, get_object_or_404
from .models import Post
from django.db.models import F  # برای شمارش بازدید (جلوگیری از Race Condition)
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def post_list_view(request):
    """
    ویو "لیست مقالات".
    تمام پست‌های "منتشر شده" را به ترتیب تاریخ ایجاد نمایش می‌دهد.
    (بهینه‌سازی شده با select_related)
    """
    posts = Post.objects.filter(is_published=True).select_related(
        'author', 'category'
    ).order_by('-created_at')
    
    return render(request, 'beautyshop_blog/post_list.html', {'posts': posts})

def post_detail_view(request, slug):
    """
    ویو "جزئیات مقاله".
    یک پست مشخص را بر اساس اسلاگ (slug) نمایش می‌دهد.
    همچنین تعداد بازدید (view_count) را یک واحد افزایش می‌دهد.
    """
    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        slug=slug, 
        is_published=True
    )
    
    # --- افزایش شمارنده بازدید ---
    # استفاده از F() expression باعث می‌شود که افزایش بازدید
    # به صورت مستقیم در دیتابیس (Atomic) انجام شود و
    # از بروز "Race Condition" (تداخل) در بازدیدهای همزمان جلوگیری می‌کند.
    post.view_count = F('view_count') + 1
    post.save(update_fields=['view_count'])
    # بازخوانی آبجکت از دیتابیس برای نمایش عدد به‌روز شده در تمپلیت
    post.refresh_from_db()
    
    # بررسی اینکه آیا کاربر لاگین کرده، این پست را لایک کرده است یا خیر
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(id=request.user.id).exists()
    
    return render(request, 'beautyshop_blog/post_detail.html', {
        'post': post,
        'is_liked': is_liked 
    })


@login_required
@require_POST  # این ویو فقط به درخواست‌های POST پاسخ می‌دهد
def like_toggle_view(request, pk):
    """
    API (AJAX) برای "لایک" و "آنلایک" کردن یک پست.
    این ویو توسط جاوا اسکریپت در صفحه جزئیات پست فراخوانی می‌شود.
    """
    try:
        post = get_object_or_404(Post, id=pk)
        
        if post.likes.filter(id=request.user.id).exists():
            # اگر کاربر قبلاً لایک کرده: آنلایک کن (حذف رابطه)
            post.likes.remove(request.user)
            liked = False
        else:
            # اگر کاربر لایک نکرده: لایک کن (ایجاد رابطه)
            post.likes.add(request.user)
            liked = True
            
        # بازگرداندن وضعیت جدید و تعداد کل لایک‌ها
        return JsonResponse({'status': 'success', 'liked': liked, 'count': post.total_likes})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)