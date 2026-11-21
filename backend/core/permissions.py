from rest_framework import permissions

from .roles import has_role, is_admin

READ_ACTIONS = {"list", "retrieve", "export", "metadata"}
EDIT_ACTIONS = {"update", "partial_update", "destroy"}


class RolePermission(permissions.BasePermission):
    """
    Role based access driven by attributes on ``BaseModelViewSet``:

    * ``read_roles``   – see every row
    * ``write_roles``  – create / update / delete (rows they can see)
    * ``create_roles`` – may only create (e.g. students submitting a complaint)
    * ``scope``        – row filter for everyone not in ``read_roles``
    * ``owner_field`` / ``owner_edit`` – non-writers may edit their own rows
    * ``ui_actions``   – per-@action role lists (+ how the portal renders them)
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_admin(user):
            return True
        act = view.action
        if act in READ_ACTIONS:
            return view.can_list(user)
        if act == "create":
            return view.can_create(user)
        if act in EDIT_ACTIONS:
            return view.can_write(user) or bool(view.owner_edit)
        return has_role(user, view.roles_for_action(act))

    def has_object_permission(self, request, view, obj):
        user = request.user
        if view.action in EDIT_ACTIONS and not view.can_write(user):
            if not view.is_owner(obj, user):
                return False
            return view.owner_edit(obj, user) if callable(view.owner_edit) else bool(view.owner_edit)
        return True
