from django.contrib import admin

from pvetool.models import (
    FAQ,
    BijlageToReply,
    CommentReply,
    CommentStatus,
    FrozenComments,
    Room
)

# Register your models here.
admin.site.register(FAQ)
admin.site.register(Room)
admin.site.register(CommentStatus)
admin.site.register(FrozenComments)
admin.site.register(CommentReply)
admin.site.register(BijlageToReply)
