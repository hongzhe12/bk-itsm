import json

from django.db.models import Q


def get_users(usernames=None, fuzzy=False):
    from blueapps.account.models import UserProperty
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    users = user_model.objects.all()
    if usernames:
        username_q = Q()
        for username in usernames:
            username_q |= Q(username__icontains=username) if fuzzy else Q(username=username)
        users = users.filter(username_q)

    users = list(users.order_by("username"))
    properties = {}
    for user_id, key, value in UserProperty.objects.filter(
        user_id__in=[user.id for user in users]
    ).values_list("user_id", "key", "value"):
        properties.setdefault(user_id, {})[key] = value

    result = []
    for user in users:
        props = properties.get(user.id, {})
        chname = props.get("chname") or user.nickname or user.username
        leader = props.get("leader") or "[]"
        try:
            leader = json.loads(leader)
        except (TypeError, ValueError):
            leader = []
        result.append(
            {
                "id": user.username,
                "username": user.username,
                "bk_username": user.username,
                "name": chname,
                "display_name": chname,
                "chname": chname,
                "leader": leader,
                "departments": [],
            }
        )
    return result
