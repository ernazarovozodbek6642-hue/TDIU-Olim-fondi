from loader import db


async def admin_allowed(user_id, permission=None):
    """Bitta markaziy admin/rol tekshiruvi."""
    return await db.has_admin_permission(str(user_id), permission)
