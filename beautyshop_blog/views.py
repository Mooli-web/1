# a_copy/beautyshop_blog/views.py

from django.shortcuts import render, get_object_or_404
from .models import Post
# --- TASK 3: Import F ---
from django.db.models import F
# --- ADDED: Imports for like view ---
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def post_list_view(request):
    # --- OPTIMIZED: Added select_related for author and category (future-proofing) ---
    posts = Post.objects.filter(is_published=True).select_related(
        'author', 'category'
    ).order_by('-created_at')
    return render(request, 'beautyshop_blog/post_list.html', {'posts': posts})

def post_detail_view(request, slug):
    # --- OPTIMIZED: Added select_related for author and category ---
    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        slug=slug, 
        is_published=True
    )
    
    # --- TASK 3: Increment view count ---
    # F() expression avoids race conditions
    post.view_count = F('view_count') + 1
    post.save(update_fields=['view_count'])
    # Refresh from DB to get the updated count for the template
    post.refresh_from_db()
    
    # --- ADDED: Check if user liked this post (for template) ---
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(id=request.user.id).exists()
    
    return render(request, 'beautyshop_blog/post_detail.html', {
        'post': post,
        'is_liked': is_liked 
    })

# --- ADDED: View to handle like/unlike toggle ---
@login_required
@require_POST
def like_toggle_view(request, pk):
    try:
        post = get_object_or_404(Post, id=pk)
        
        if post.likes.filter(id=request.user.id).exists():
            # User has liked, so unlike
            post.likes.remove(request.user)
            liked = False
        else:
            # User has not liked, so like
            post.likes.add(request.user)
            liked = True
            
        return JsonResponse({'status': 'success', 'liked': liked, 'count': post.total_likes})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)