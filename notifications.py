from datetime import datetime
import uuid

from sheets import (
    get_all_records,
    append_record,
    update_record,
)


EVENTS_SHEET = "Events"
USERS_SHEET = "Users"
NOTIFICATIONS_SHEET = "Notification"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):

    if value is None:
        return ""

    return str(value).strip()


def normalize_lower(value):

    return normalize(value).lower()


# ============================================================
# PHONE
# ============================================================

def normalize_phone(phone):

    phone = normalize(phone)

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+", "")
    )

    if phone.startswith("0"):

        return "27" + phone[1:]

    if phone.startswith("27"):

        return phone

    if len(phone) == 9:

        return "27" + phone

    return phone


# ============================================================
# MULTI VALUE
# ============================================================

def split_values(value):

    if not value:
        return []

    value = str(value)

    for separator in ["|", ";"]:
        value = value.replace(
            separator,
            ","
        )

    return [
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    ]


def split_categories(value):

    return split_values(value)


def split_areas(value):

    return split_values(value)


# ============================================================
# MATCHING
# ============================================================

def user_matches_event(
    user,
    event,
):

    active = normalize_lower(
        user.get("active")
    )

    if active and active not in [
        "true",
        "yes",
        "1",
        "active",
    ]:

        return False

    event_area = normalize_lower(
        event.get("area")
    )

    event_category = normalize_lower(
        event.get("category")
    )

    if not event_area:
        return False

    if not event_category:
        return False

    user_areas = split_areas(
        user.get("areas")
    )

    user_categories = split_categories(
        user.get("categories")
    )

    if event_area not in user_areas:

        return False

    if event_category not in user_categories:

        return False

    return True


# ============================================================
# FIND PENDING EVENT
# ============================================================

def get_pending_event():

    events = get_all_records(
        EVENTS_SHEET
    )

    for event in events:

        status = normalize_lower(
            event.get("status")
        )

        notification_status = normalize_lower(
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
# FIND MATCHING USERS
# ============================================================

def get_matching_users(event):

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
# CHANNEL ELIGIBILITY
# ============================================================

# ============================================================
# NOTIFICATION CHANNELS
# ============================================================

def is_yes(value):
    """
    Treat common Google Form values as Yes.
    """
    return normalize(value).lower() in [
        "yes",
        "true",
        "1",
        "y",
    ]


def get_notification_channels(user):
    """
    Determine which notification channels this user
    is allowed to receive.

    Possible results:

        ["WhatsApp"]
        ["SMS"]
        ["WhatsApp", "SMS"]
        []

    The user's explicit opt-in fields are respected.
    """

    channels = []

    channel_preference = normalize(
        user.get("notification_channel")
    ).lower()

    whatsapp_opt_in = is_yes(
        user.get("whatsapp_opt_in")
    )

    sms_opt_in = is_yes(
        user.get("sms_opt_in")
    )

    # --------------------------------------------------------
    # WhatsApp
    # --------------------------------------------------------

    if (
        whatsapp_opt_in
        and channel_preference in [
            "whatsapp",
            "both",
            "whatsapp and sms",
            "sms and whatsapp",
        ]
    ):
        channels.append("WhatsApp")

    # --------------------------------------------------------
    # SMS
    # --------------------------------------------------------

    if (
        sms_opt_in
        and channel_preference in [
            "sms",
            "both",
            "whatsapp and sms",
            "sms and whatsapp",
        ]
    ):
        channels.append("SMS")

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    # If Notification Channel is blank, use the
    # explicit opt-in fields.

    if not channel_preference:

        if whatsapp_opt_in:
            channels.append("WhatsApp")

        if sms_opt_in:
            channels.append("SMS")

    return channels


def get_notification_channel(user):
    """
    Backwards-compatible helper.

    Returns the first available channel.

    New code should use get_notification_channels()
    because a user can select BOTH.
    """

    channels = get_notification_channels(user)

    if channels:
        return channels[0]

    return ""
# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================


# ============================================================
# NOTIFICATION KEY
# ============================================================

def build_notification_key(
    event,
    user,
    channel,
):

    event_name = normalize(
        event.get("event_name")
    )

    event_date = normalize(
        event.get("event_date")
    )

    event_time = normalize(
        event.get("event_time")
    )

    venue = normalize(
        event.get("venue")
    )

    phone = normalize_phone(
        user.get("phone")
    )

    return (
        f"{event_name}|"
        f"{event_date}|"
        f"{event_time}|"
        f"{venue}|"
        f"{phone}|"
        f"{channel.lower()}"
    )


# ============================================================
# MESSAGE
# ============================================================

def build_message(event):

    return (
        "🎉 Event Alert!\n\n"
        f"{normalize(event.get('event_name'))}\n"
        f"Date: {normalize(event.get('event_date'))}\n"
        f"Time: {normalize(event.get('event_time'))}\n"
        f"Venue: {normalize(event.get('venue'))}\n"
        f"Area: {normalize(event.get('area'))}\n\n"
        "More details coming soon."
    )


# ============================================================
# DUPLICATE
# ============================================================

def notification_exists(
    existing_notifications,
    notification_key,
):

    for notification in existing_notifications:

        existing_key = normalize(
            notification.get(
                "Notification Key"
            )
        )

        if existing_key == notification_key:

            return True

    return False


# ============================================================
# CREATE
# ============================================================

def create_notification(
    event,
    user,
    channel,
):

    notification_id = (
        "NOT-"
        + uuid.uuid4().hex[:10].upper()
    )

    notification_key = (
        build_notification_key(
            event,
            user,
            channel,
        )
    )

    phone = normalize_phone(
        user.get("phone")
    )

    record = {

        "Notification ID":
            notification_id,

        "Event Name":
            normalize(
                event.get("event_name")
            ),

        "Event Date":
            normalize(
                event.get("event_date")
            ),

        "Event Time":
            normalize(
                event.get("event_time")
            ),

        "Venue ":
            normalize(
                event.get("venue")
            ),

        "Area":
            normalize(
                event.get("area")
            ),

        "Category":
            normalize(
                event.get("category")
            ),

        "User Name":
            normalize(
                user.get("name")
            ),

        "Phone Number":
            phone,

        "Notification Channel":
            channel,

        "Message":
            build_message(event),

        "Status":
            "Pending",

        "Created At":
            datetime.now().isoformat(),

        "Sent At":
            "",

        "Notification Key":
            notification_key,

        "Retry Count":
            0,

        "Last Error":
            "",

        "Processed At":
            "",

        "Twilio SID":
            "",
    }

    append_record(
        NOTIFICATIONS_SHEET,
        record,
    )

    return {
        "status": "created",
        "notification_key":
            notification_key,
        "notification_id":
            notification_id,
        "channel":
            channel,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    event = get_pending_event()

    if not event:

        print(
            "No pending event."
        )

        return

    users = get_matching_users(
        event
    )

    existing_notifications = (
        get_all_records(
            NOTIFICATIONS_SHEET
        )
    )

    created = 0
    duplicates = 0

    for user in users:

        channels = get_notification_channels(
            user
        )

        print(
            f"{user.get('name')}: "
            f"{channels}"
        )

        for channel in channels:

            notification_key = (
                build_notification_key(
                    event,
                    user,
                    channel,
                )
            )

            if notification_exists(
                existing_notifications,
                notification_key,
            ):

                duplicates += 1

                continue

            result = create_notification(
                event,
                user,
                channel,
            )

            existing_notifications.append(
                {
                    "Notification Key":
                        notification_key
                }
            )

            created += 1

            print(
                "CREATED:",
                result,
            )

    if created > 0 or duplicates > 0:

        row_number = event.get(
            "Row number"
        )

        if row_number:

            update_record(
                EVENTS_SHEET,
                int(row_number),
                {
                    "notification_status":
                        "Processed",
                },
            )

    print()
    print(
        f"Notifications created: {created}"
    )

    print(
        f"Duplicates blocked: {duplicates}"
    )


if __name__ == "__main__":

    main()