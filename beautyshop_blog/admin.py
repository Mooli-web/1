# beautyshop_blog/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن beautyshop_blog.
"""

from django.contrib import admin
from .models import Post, Category
from jalali_date.admin import ModelAdminJalaliMixin # <-- اضافه شد

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    کلاس مدیریتی برای "دسته‌بندی".
    """
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # اسلاگ به صورت خودکار از نام پر می‌شود
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(ModelAdminJalaliMixin, admin.ModelAdmin): # <-- اصلاح شد
    """
    کلاس مدیریتی برای "پست".
    """
    list_display = ('title', 'author', 'category', 'created_at', 'is_published', 'view_count', 'total_likes')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    raw_id_fields = ('author', 'category')
    
    # --- تنظیمات نمایش فیلدهای لایک ---
    
    # 1. 'total_likes' (که یک property است) فقط خواندنی است
    readonly_fields = ('total_likes',)
    
    # 2. فیلد 'likes' (رابطه ManyToMany) را پنهان کن.
    # دلیل: ادمین نباید به صورت دستی "لایک کاربر" را اضافه کند.
    # ادمین برای افزودن لایک باید از فیلد 'fake_like_count' استفاده کند.
    exclude = ('likes',) 
    
    # 3. فیلدهای 'view_count' و 'fake_like_count' به صورت خودکار
    #    به عنوان فیلد عددی قابل ویرایش (در fieldsets) نمایش داده می‌شوند.

    def total_likes(self, obj):
        """
        فراخوانی property مدل برای نمایش در list_display.
        """
        return obj.total_likes
    total_likes.short_description = "تعداد کل لایک‌ها (واقعی + دستی)"