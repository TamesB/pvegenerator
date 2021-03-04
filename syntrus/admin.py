from django.contrib import admin
from syntrus.models import (
    FAQ,
    Room,
    CommentStatus,
    FrozenComments,
    CommentReply,
    BijlageToReply,
)

# Register your models here.
admin.site.register(FAQ)
admin.site.register(Room)
admin.site.register(CommentStatus)
admin.site.register(FrozenComments)
admin.site.register(CommentReply)
admin.site.register(BijlageToReply)
