from datetime import datetime
import uuid

from sheets import (
    get_all_records,
    append_record,
    update_record,
)


FORM_SHEET = "Form Responses 5"
USERS_SHEET = "Users"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize_lower(value):
    return normalize(value).lower()


def split_values(value):
    """
    Convert:

        Music
        Music, Sports
        Music | Sports
        Music; Sports

    into:

        ["Music", "Sports"]
    """

    if not value:
        return []

    value = str(value)

    for separator in ["|", ";"]:
        value = value.replace(separator, ",")

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def normalize_list(values):

    result = []
    seen = set()

    for value in values:

        cleaned = normalize(value)

        if not cleaned:
            continue

        key = cleaned.lower()

        if key not in seen:

            seen.add(key)
            result.append(cleaned)

    return result


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(phone):

    if phone is None:
        return ""

    phone = str(phone).strip()

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0"):
        phone = "27" + phone[1:]

    elif not phone.startswith("27"):
        phone = "27" + phone

    return phone


# ============================================================
# USER ID
# ============================================================

def generate_user_id():

    return (
        "USR-"
        + uuid.uuid4().hex[:8].upper()
    )


# ============================================================
# FIND USER
# ============================================================

def find_user_by_phone(phone):

    users = get_all_records(
        USERS_SHEET
    )

    phone = normalize_phone(phone)

    if not phone:
        return None

    for user in users:

        existing_phone = normalize_phone(
            user.get("phone")
        )

        if existing_phone == phone:

            return user

    return None


# ============================================================
# CREATE USER
# ============================================================

def create_user(form):

    phone = normalize_phone(
        form.get("Phone Number")
    )

    name = normalize(
        form.get("Name")
    )

    areas = normalize_list(
        split_values(
            form.get("Areas")
        )
    )

    categories = normalize_list(
        split_values(
            form.get("Categories")
        )
    )

    channel = normalize(
        form.get(
            "Notification Channel"
        )
    )

    whatsapp_opt_in = normalize(
        form.get(
            "WhatsApp Opt-In"
        )
    )

    sms_opt_in = normalize(
        form.get(
            "SMS Opt-In"
        )
    )

    user = {

        "user_id":
            generate_user_id(),

        "name":
            name,

        "phone":
            phone,

        "areas":
            ", ".join(areas),

        "categories":
            ", ".join(categories),

        "notification_channel":
            channel,

        "active":
            "Yes",

        "whatsapp_opt_in":
            whatsapp_opt_in,

        "sms_opt_in":
            sms_opt_in,

        "created_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
    }

    append_record(
        USERS_SHEET,
        user,
    )

    return user


# ============================================================
# UPDATE USER
# ============================================================

def update_user(user, form):

    row_number = user.get(
        "Row number"
    )

    if not row_number:

        raise RuntimeError(
            "User has no Row number."
        )

    existing_areas = user.get(
        "areas",
        "",
    )

    existing_categories = user.get(
        "categories",
        "",
    )

    new_areas = split_values(
        form.get("Areas")
    )

    new_categories = split_values(
        form.get("Categories")
    )

    merged_areas = normalize_list(
        split_values(existing_areas)
        + new_areas
    )

    merged_categories = normalize_list(
        split_values(existing_categories)
        + new_categories
    )

    updates = {

        "name":
            normalize(
                form.get(
                    "Name",
                    user.get("name", ""),
                )
            ),

        "areas":
            ", ".join(
                merged_areas
            ),

        "categories":
            ", ".join(
                merged_categories
            ),

        "notification_channel":
            normalize(
                form.get(
                    "Notification Channel",
                    user.get(
                        "notification_channel",
                        "",
                    ),
                )
            ),

        "whatsapp_opt_in":
            normalize(
                form.get(
                    "WhatsApp Opt-In",
                    user.get(
                        "whatsapp_opt_in",
                        "",
                    ),
                )
            ),

        "sms_opt_in":
            normalize(
                form.get(
                    "SMS Opt-In",
                    user.get(
                        "sms_opt_in",
                        "",
                    ),
                )
            ),

        "active":
            "Yes",
    }

    update_record(
        USERS_SHEET,
        row_number,
        updates,
    )

    user.update(updates)

    return user


# ============================================================
# PROCESS ONE FORM RESPONSE
# ============================================================

def process_form_response(form):

    phone = normalize_phone(
        form.get("Phone Number")
    )

    if not phone:

        return {
            "status": "skipped",
            "reason": "Missing phone number",
        }

    name = normalize(
        form.get("Name")
    )

    if not name:

        return {
            "status": "skipped",
            "reason": "Missing name",
        }

    areas = split_values(
        form.get("Areas")
    )

    categories = split_values(
        form.get("Categories")
    )

    if not areas:

        return {
            "status": "skipped",
            "reason": "No areas selected",
        }

    if not categories:

        return {
            "status": "skipped",
            "reason": "No categories selected",
        }

    channel = normalize_lower(
        form.get(
            "Notification Channel"
        )
    )

    whatsapp_opt_in = normalize_lower(
        form.get(
            "WhatsApp Opt-In"
        )
    )

    sms_opt_in = normalize_lower(
        form.get(
            "SMS Opt-In"
        )
    )

    # --------------------------------------------------------
    # VALID CHANNEL
    # --------------------------------------------------------

    valid_channels = [
        "whatsapp",
        "sms",
        "both",
    ]

    if channel not in valid_channels:

        return {
            "status": "skipped",
            "reason": (
                "Invalid notification channel: "
                + channel
            ),
        }

    # --------------------------------------------------------
    # FIND EXISTING USER
    # --------------------------------------------------------

    user = find_user_by_phone(
        phone
    )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if not user:

        user = create_user(
            form
        )

        return {
            "status": "created",
            "user_id":
                user.get("user_id"),
            "phone":
                phone,
            "channel":
                channel,
        }

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    user = update_user(
        user,
        form,
    )

    return {
        "status": "updated",
        "user_id":
            user.get("user_id"),
        "phone":
            phone,
        "channel":
            channel,
    }


# ============================================================
# SYNC ALL RESPONSES
# ============================================================

def sync_subscriptions():

    responses = get_all_records(
        FORM_SHEET
    )

    print("=" * 60)
    print("USER SYNCHRONIZATION")
    print("=" * 60)

    print(
        f"Form responses: {len(responses)}"
    )

    created = 0
    updated = 0
    skipped = 0

    for response in responses:

        result = process_form_response(
            response
        )

        status = result.get(
            "status"
        )

        if status == "created":

            created += 1

        elif status == "updated":

            updated += 1

        else:

            skipped += 1

        print()
        print(
            "RESULT:",
            result
        )

    print()
    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)

    print(
        f"Created: {created}"
    )

    print(
        f"Updated: {updated}"
    )

    print(
        f"Skipped: {skipped}"
    )

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }


# ============================================================
# IMPORTANT
# ADMIN DASHBOARD IMPORTS main()
# ============================================================

def main():

    return sync_subscriptions()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    main()
