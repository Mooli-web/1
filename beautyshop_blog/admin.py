# beautyshop_blog/admin.py
from django.contrib import admin
from .models import Post, Category
from jalali_date.admin import ModelAdminJalaliMixin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} 
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'title', 
        'author', 
        'category', 
        'created_at', 
        'is_published', 
        'view_count', 
        'total_likes_display'
    )
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    raw_id_fields = ('author', 'category')
    
    # فیلد کش شده را فقط نمایش می‌دهیم (چون خودکار آپدیت می‌شود)
    readonly_fields = ('cached_like_count', 'total_likes_display')
    exclude = ('likes',) 

    def total_likes_display(self, obj):
        return obj.total_likes
    
    total_likes_display.short_description = "مجموع لایک‌ها"
    # حالا می‌توانیم بر اساس تعداد واقعی لایک سورت کنیم (چیزی که قبلاً سخت بود)
    total_likes_display.admin_order_field = 'cached_like_count'