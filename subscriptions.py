from sheets import get_all_records


USERS_SHEET = "Users"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


# ============================================================
# BOOLEAN
# ============================================================

def is_true(value):
    return normalize(value) in {
        "yes",
        "true",
        "1",
        "active",
        "on",
    }


# ============================================================
# LIST PARSER
# ============================================================

def split_values(value):
    """
    Convert a Google Sheets field into a normalized list.

    Supports:

        Sports
        Sports, Music
        Sports | Music
        Sports; Music
    """

    if not value:
        return []

    value = str(value)

    for separator in ["|", ";"]:
        value = value.replace(separator, ",")

    return [
        normalize(item)
        for item in value.split(",")
        if normalize(item)
    ]


# ============================================================
# USER ACTIVE / SUBSCRIBED
# ============================================================

def user_is_subscribed(user):

    active = is_true(
        user.get("active")
    )

    whatsapp_opt_in = is_true(
        user.get("whatsapp_opt_in")
    )

    return active and whatsapp_opt_in


# ============================================================
# USER AREAS
# ============================================================

def get_user_areas(user):

    return split_values(
        user.get("area")
    )


# ============================================================
# USER CATEGORIES
# ============================================================

def get_user_categories(user):

    return split_values(
        user.get("categories")
    )


# ============================================================
# AREA MATCH
# ============================================================

def user_subscribed_to_area(
    user,
    event_area,
):

    event_area = normalize(
        event_area
    )

    if not event_area:
        return False

    user_areas = get_user_areas(
        user
    )

    return event_area in user_areas


# ============================================================
# CATEGORY MATCH
# ============================================================

def user_subscribed_to_category(
    user,
    event_category,
):

    event_category = normalize(
        event_category
    )

    if not event_category:
        return False

    user_categories = get_user_categories(
        user
    )

    return event_category in user_categories


# ============================================================
# USER CHANNEL
# ============================================================

def user_supports_whatsapp(user):

    channel = normalize(
        user.get(
            "notification_channel"
        )
    )

    return channel in {
        "whatsapp",
        "both",
    }


# ============================================================
# TEST
# ============================================================

def main():

    users = get_all_records(
        USERS_SHEET
    )

    print()
    print("=" * 60)
    print("SUBSCRIPTION ENGINE TEST")
    print("=" * 60)
    print()

    print(
        f"Users: {len(users)}"
    )

    print()

    for user in users:

        print(
            f"User: {user.get('name')}"
        )

        print(
            f"Areas: "
            f"{get_user_areas(user)}"
        )

        print(
            f"Categories: "
            f"{get_user_categories(user)}"
        )

        print(
            f"Active: "
            f"{user.get('active')}"
        )

        print(
            f"WhatsApp Opt-In: "
            f"{user.get('whatsapp_opt_in')}"
        )

        print(
            f"Subscribed: "
            f"{user_is_subscribed(user)}"
        )

        print(
            f"Sports: "
            f"{user_subscribed_to_category(user, 'Sports')}"
        )

        print(
            f"Music: "
            f"{user_subscribed_to_category(user, 'Music')}"
        )

        print(
            f"KwaMhlanga: "
            f"{user_subscribed_to_area(user, 'KwaMhlanga')}"
        )

        print(
            f"Middelburg: "
            f"{user_subscribed_to_area(user, 'Middelburg')}"
        )

        print(
            f"WhatsApp: "
            f"{user_supports_whatsapp(user)}"
        )

        print("-" * 60)


if __name__ == "__main__":
    main()