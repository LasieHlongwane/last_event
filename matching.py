from sheets import get_all_records


EVENTS_SHEET = "Events"
USERS_SHEET = "Users"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    """
    Normalize a value for reliable comparison.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


# ============================================================
# AREA NORMALIZATION
# ============================================================

def normalize_area(value):
    """
    Normalize an area while preserving the relationship
    between village and main area.

    Examples:

        "Zakheni, KwaMhlanga"
        -> "zakheni, kwamhlanga"

        "KwaMhlanga"
        -> "kwamhlanga"
    """

    value = normalize(value)

    if not value:
        return ""

    # Clean spacing around commas.
    parts = [
        part.strip()
        for part in value.split(",")
        if part.strip()
    ]

    return ", ".join(parts)


# ============================================================
# PARSE AREA
# ============================================================

def parse_area(value):
    """
    Convert an area into:

        {
            "village": "...",
            "main_area": "...",
            "full_area": "..."
        }

    Examples:

        Zakheni, KwaMhlanga

        ->
        {
            "village": "zakheni",
            "main_area": "kwamhlanga",
            "full_area": "zakheni, kwamhlanga"
        }


        KwaMhlanga

        ->
        {
            "village": "",
            "main_area": "kwamhlanga",
            "full_area": "kwamhlanga"
        }
    """

    area = normalize_area(value)

    if not area:
        return {
            "village": "",
            "main_area": "",
            "full_area": "",
        }

    parts = [
        part.strip()
        for part in area.split(",")
        if part.strip()
    ]

    # --------------------------------------------------------
    # Main area only
    # --------------------------------------------------------

    if len(parts) == 1:

        return {
            "village": "",
            "main_area": parts[0],
            "full_area": parts[0],
        }

    # --------------------------------------------------------
    # Village + main area
    # --------------------------------------------------------

    village = parts[0]
    main_area = parts[-1]

    return {
        "village": village,
        "main_area": main_area,
        "full_area": area,
    }


# ============================================================
# SPLIT MULTIPLE USER AREAS
# ============================================================

def split_areas(value):
    """
    Split multiple subscribed areas.

    IMPORTANT:

    We deliberately DO NOT split on commas.

    This means:

        "Zakheni, KwaMhlanga | Leratong, KwaMhlanga"

    becomes:

        [
            "zakheni, kwamhlanga",
            "leratong, kwamhlanga"
        ]

    and NOT:

        [
            "zakheni",
            "kwamhlanga",
            "leratong",
            "kwamhlanga"
        ]

    Multiple areas should therefore be stored using:

        |
    
    or:

        ;
    """

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    # Convert semicolon to pipe.
    value = value.replace(";", "|")

    areas = []

    for item in value.split("|"):

        area = normalize_area(item)

        if area:
            areas.append(area)

    return areas


# ============================================================
# SPLIT CATEGORIES
# ============================================================

def split_categories(value):
    """
    Split multiple categories.

    Categories do not contain commas as part of their
    identity, so comma/pipe/semicolon separation is safe.
    """

    if value is None:
        return []

    value = str(value).strip()

    if not value:
        return []

    for separator in ["|", ";"]:
        value = value.replace(
            separator,
            ","
        )

    return [
        normalize(item)
        for item in value.split(",")
        if normalize(item)
    ]


# Backwards-compatible helper
def split_values(value):
    """
    Generic value splitter.

    Used mainly for categories.

    Do NOT use this for areas because area names contain
    commas.
    """

    return split_categories(value)


# ============================================================
# BOOLEAN HELPERS
# ============================================================

def is_truthy(value):
    """
    Understand common Google Forms / Google Sheets
    boolean values.
    """

    return normalize(value) in {
        "yes",
        "true",
        "1",
        "active",
        "on",
    }


# ============================================================
# USER ACTIVE CHECK
# ============================================================

def user_is_active(user):
    """
    Users are considered active when:

    - active = Yes
    - active = True
    - active = 1
    - active = Active

    If the field is empty, treat the user as active for
    backwards compatibility.
    """

    active = normalize(
        user.get("active")
    )

    if not active:
        return True

    return is_truthy(active)


# ============================================================
# WHATSAPP PERMISSION
# ============================================================

def user_can_receive_whatsapp(user):
    """
    Determine whether the user can receive WhatsApp
    notifications.

    Requirements:

    1. WhatsApp opt-in is enabled.
    2. Notification channel allows WhatsApp.
    """

    whatsapp_opt_in = normalize(
        user.get("whatsapp_opt_in")
    )

    channel = normalize(
        user.get("notification_channel")
    )

    opt_in_allowed = whatsapp_opt_in in {
        "yes",
        "true",
        "1",
    }

    channel_allowed = channel in {
        "whatsapp",
        "both",
    }

    return (
        opt_in_allowed
        and channel_allowed
    )


# ============================================================
# AREA MATCHING
# ============================================================

def area_matches(
    user_area,
    event_area,
):
    """
    Determine whether a user's area matches an event area.

    Supported matching levels:

    ----------------------------------------------------------
    MAIN-AREA EVENT
    ----------------------------------------------------------

    Event:

        KwaMhlanga

    User:

        Zakheni, KwaMhlanga

    Result:

        MATCH


    ----------------------------------------------------------
    VILLAGE-SPECIFIC EVENT
    ----------------------------------------------------------

    Event:

        Zakheni, KwaMhlanga

    User:

        Zakheni, KwaMhlanga

    Result:

        MATCH


    Event:

        Zakheni, KwaMhlanga

    User:

        Leratong, KwaMhlanga

    Result:

        NO MATCH


    ----------------------------------------------------------
    DIFFERENT MAIN AREA
    ----------------------------------------------------------

    Event:

        Zakheni, KwaMhlanga

    User:

        Zakheni, Moloto

    Result:

        NO MATCH
    """

    user = parse_area(
        user_area
    )

    event = parse_area(
        event_area
    )

    if not user["main_area"]:
        return False

    if not event["main_area"]:
        return False

    # --------------------------------------------------------
    # Main area MUST always match.
    # --------------------------------------------------------

    if (
        user["main_area"]
        != event["main_area"]
    ):
        return False

    # --------------------------------------------------------
    # Event targets the entire main area.
    # --------------------------------------------------------

    if not event["village"]:
        return True

    # --------------------------------------------------------
    # Event targets a specific village.
    # --------------------------------------------------------

    return (
        user["village"]
        == event["village"]
    )


# ============================================================
# USER AREA MATCHING
# ============================================================

def user_has_matching_area(
    user,
    event,
):
    """
    Check all areas subscribed to by the user.

    A user may subscribe to:

        Zakheni, KwaMhlanga |
        Leratong, KwaMhlanga |
        Suncity, KwaMhlanga

    An event can then target:

        KwaMhlanga

    or:

        Zakheni, KwaMhlanga
    """

    event_area = normalize_area(
        event.get("area")
    )

    if not event_area:
        return False

    user_areas = split_areas(
        user.get("areas")
    )

    for user_area in user_areas:

        if area_matches(
            user_area,
            event_area,
        ):
            return True

    return False


# ============================================================
# FIND PENDING EVENT
# ============================================================

def find_pending_event():
    """
    Find the first event waiting for notifications.
    """

    events = get_all_records(
        EVENTS_SHEET
    )

    for event in events:

        status = normalize(
            event.get("status")
        )

        notification_status = normalize(
            event.get(
                "notification_status"
            )
        )

        if (
            status == "active"
            and notification_status == "pending"
        ):
            return event

    return None


# ============================================================
# MATCH USER TO EVENT
# ============================================================

def user_matches_event(
    user,
    event,
):
    """
    Determine whether a user should receive a notification.

    Matching requires:

        1. User is active.
        2. User's main area matches event's main area.
        3. If event is village-specific, user's village
           must also match.
        4. Event category matches user's category.
        5. User has WhatsApp permission.

    Examples:

    ----------------------------------------------------------
    EVENT
    ----------------------------------------------------------

    area = "KwaMhlanga"
    category = "Music (Events)"

    Matches:

        Zakheni, KwaMhlanga
        Leratong, KwaMhlanga
        Suncity, KwaMhlanga
        KwaMhlanga Central, KwaMhlanga

    ----------------------------------------------------------
    EVENT
    ----------------------------------------------------------

    area = "Zakheni, KwaMhlanga"

    Matches:

        Zakheni, KwaMhlanga

    Does NOT match:

        Leratong, KwaMhlanga
        Suncity, KwaMhlanga
    """

    # --------------------------------------------------------
    # ACTIVE USER
    # --------------------------------------------------------

    if not user_is_active(user):
        return False

    # --------------------------------------------------------
    # EVENT VALUES
    # --------------------------------------------------------

    event_area = normalize_area(
        event.get("area")
    )

    event_category = normalize(
        event.get("category")
    )

    if not event_area:
        return False

    if not event_category:
        return False

    # --------------------------------------------------------
    # AREA MATCH
    # --------------------------------------------------------

    if not user_has_matching_area(
        user,
        event,
    ):
        return False

    # --------------------------------------------------------
    # CATEGORY MATCH
    # --------------------------------------------------------

    user_categories = split_categories(
        user.get("categories")
    )

    if event_category not in user_categories:
        return False

    # --------------------------------------------------------
    # WHATSAPP PERMISSION
    # --------------------------------------------------------

    if not user_can_receive_whatsapp(
        user
    ):
        return False

    return True


# ============================================================
# FIND MATCHING USERS
# ============================================================

def find_matching_users(event):
    """
    Return every user who should receive the event.
    """

    users = get_all_records(
        USERS_SHEET
    )

    matches = []

    for user in users:

        if user_matches_event(
            user,
            event,
        ):
            matches.append(user)

    return matches


# ============================================================
# TEST AREA MATCHING
# ============================================================

def test_area_matching():
    """
    Test the area hierarchy without needing Google Sheets.

    This is useful while developing the MVP.
    """

    print()
    print("=" * 70)
    print("AREA HIERARCHY MATCHING TEST")
    print("=" * 70)

    test_cases = [
        (
            "Zakheni, KwaMhlanga",
            "KwaMhlanga",
            True,
        ),

        (
            "Leratong, KwaMhlanga",
            "KwaMhlanga",
            True,
        ),

        (
            "Suncity, KwaMhlanga",
            "KwaMhlanga",
            True,
        ),

        (
            "Zakheni, KwaMhlanga",
            "Zakheni, KwaMhlanga",
            True,
        ),

        (
            "Leratong, KwaMhlanga",
            "Zakheni, KwaMhlanga",
            False,
        ),

        (
            "Suncity, KwaMhlanga",
            "Zakheni, KwaMhlanga",
            False,
        ),

        (
            "Zakheni, Moloto",
            "Zakheni, KwaMhlanga",
            False,
        ),
    ]

    for (
        user_area,
        event_area,
        expected,
    ) in test_cases:

        result = area_matches(
            user_area,
            event_area,
        )

        status = (
            "PASS"
            if result == expected
            else "FAIL"
        )

        print()
        print(
            f"{status}: "
            f"User [{user_area}] "
            f"-> Event [{event_area}] "
            f"= {result}"
        )

    print()
    print("=" * 70)


# ============================================================
# TEST MULTIPLE USER AREAS
# ============================================================

def test_multiple_areas():

    print()
    print("=" * 70)
    print("MULTIPLE AREA PARSING TEST")
    print("=" * 70)

    value = (
        "Zakheni, KwaMhlanga | "
        "Leratong, KwaMhlanga | "
        "Suncity, KwaMhlanga"
    )

    areas = split_areas(
        value
    )

    print()

    print(
        "Original:"
    )

    print(value)

    print()

    print(
        "Parsed areas:"
    )

    for area in areas:

        print(
            f" - {area}"
        )

    print()

    print(
        "Expected: 3 areas"
    )

    print(
        "Actual:",
        len(areas)
    )

    print()
    print("=" * 70)


# ============================================================
# TEST PENDING EVENT
# ============================================================

def main():

    print("=" * 70)
    print(
        "MULTI-AREA / VILLAGE-SPECIFIC MATCHING TEST"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Test area parser first.
    # --------------------------------------------------------

    test_multiple_areas()

    # --------------------------------------------------------
    # Test hierarchy.
    # --------------------------------------------------------

    test_area_matching()

    # --------------------------------------------------------
    # Find pending event.
    # --------------------------------------------------------

    event = find_pending_event()

    if not event:

        print()
        print(
            "No pending events found."
        )

        return

    print()
    print("EVENT")
    print("-" * 70)

    print(
        "ID:",
        event.get("event_id"),
    )

    print(
        "Name:",
        event.get("event_name"),
    )

    print(
        "Area:",
        event.get("area"),
    )

    print(
        "Category:",
        event.get("category"),
    )

    print(
        "Status:",
        event.get("status"),
    )

    print(
        "Notification:",
        event.get(
            "notification_status"
        ),
    )

    # --------------------------------------------------------
    # Matching
    # --------------------------------------------------------

    matches = find_matching_users(
        event
    )

    print()
    print(
        f"Matched users: {len(matches)}"
    )

    print()

    if not matches:

        print(
            "No users matched this event."
        )

        return

    # --------------------------------------------------------
    # Display matches
    # --------------------------------------------------------

    for user in matches:

        print(
            f"ID:         {user.get('user_id')}"
        )

        print(
            f"Name:       {user.get('name')}"
        )

        print(
            f"Phone:      {user.get('phone')}"
        )

        print(
            f"Areas:      {user.get('areas')}"
        )

        print(
            f"Categories: {user.get('categories')}"
        )

        print(
            f"Channel:    {user.get('notification_channel')}"
        )

        print(
            f"WhatsApp:   {user.get('whatsapp_opt_in')}"
        )

        print(
            f"Active:     {user.get('active')}"
        )

        print("-" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()