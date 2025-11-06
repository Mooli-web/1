# a_copy/beautyshop_blog/admin.py

from django.contrib import admin
from .models import Post, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # --- 'total_likes' property will still work ---
    list_display = ('title', 'author', 'category', 'created_at', 'is_published', 'view_count', 'total_likes')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    raw_id_fields = ('author', 'category')
    
    # --- THIS IS THE FIX ---
    
    # 1. 'total_likes' فقط خواندنی است (چون محاسبه می‌شود)
    readonly_fields = ('total_likes',)
    
    # 2. فیلد پیچیده 'likes' (انتخاب کاربر) را پنهان می‌کنیم
    exclude = ('likes',) 
    
    # 3. فیلدهای 'view_count' و 'fake_like_count' به صورت خودکار
    #    به عنوان فیلد عددی قابل ویرایش نمایش داده می‌شوند.

    def total_likes(self, obj):
        # این تابع اکنون لایک‌های واقعی + دستی را برمی‌گرداند
        return obj.total_likes
    total_likes.short_description = "تعداد کل لایک‌ها"