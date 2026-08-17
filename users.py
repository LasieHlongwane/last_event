
import uuid

from sheets import get_all_records, append_record


# =========================================================
# SOURCE → USERS DATABASE
# =========================================================

SOURCE_SHEET = "Form Responses 4"
USERS_SHEET = "Users"


# =========================================================
# HELPERS
# =========================================================

def clean(value):
    """
    Convert a Google Sheets value into clean text.
    """

    if value is None:
        return ""

    return str(value).strip()


def generate_user_id():
    """
    Generate a unique user ID.
    """

    return f"USR-{uuid.uuid4().hex[:8].upper()}"


# =========================================================
# FIND EXISTING USER
# =========================================================

def user_exists(phone):
    """
    Check whether a user already exists using their phone
    number.

    Phone number is our primary duplicate check because
    users may submit the registration form more than once.
    """

    users = get_all_records(USERS_SHEET)

    phone = clean(phone)

    if not phone:
        return False

    for user in users:

        existing_phone = clean(
            user.get("phone", "")
        )

        if existing_phone == phone:
            return True

    return False


# =========================================================
# CONVERT FORM RESPONSE
# =========================================================

def build_user_record(form_response):
    """
    Convert one Google Form response into a Users record.
    """

    phone = clean(
        form_response.get("Phone number")
    )

    name = clean(
        form_response.get("Name")
    )

    email = clean(
        form_response.get("Email")
    )

    area = clean(
        form_response.get(
            "What areas would you like to receive notifications from?"
        )
    )

    categories = clean(
        form_response.get(
            "What events interest you?"
        )
    )

    notification_channel = clean(
        form_response.get(
            "Preferred notification method"
        )
    )

    whatsapp_opt_in = clean(
        form_response.get(
            "WhatsApp notification"
        )
    )

    return {
        "user_id": generate_user_id(),
        "name": name,
        "phone": phone,
        "email": email,
        "area": area,
        "categories": categories,
        "notification_channel": notification_channel,
        "active": "Yes",
        "whatsapp_opt_in": whatsapp_opt_in,
        "created_at": clean(
            form_response.get("Timestamp")
        ),
    }


# =========================================================
# SYNC USERS
# =========================================================

def sync_users():
    """
    Read Google Form responses and add new users to
    the Users sheet.

    Existing phone numbers are skipped.
    """

    form_responses = get_all_records(
        SOURCE_SHEET
    )

    users_added = 0
    users_skipped = 0

    for response in form_responses:

        phone = clean(
            response.get("Phone number")
        )

        # Ignore incomplete submissions.
        if not phone:
            users_skipped += 1
            continue

        # Prevent duplicate users.
        if user_exists(phone):
            users_skipped += 1
            continue

        user = build_user_record(
            response
        )

        append_record(
            USERS_SHEET,
            user,
        )

        users_added += 1

    return {
        "users_added": users_added,
        "users_skipped": users_skipped,
    }


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("USER SYNCHRONIZATION")
    print("=" * 60)

    result = sync_users()

    print()
    print(
        f"Users added: {result['users_added']}"
    )

    print(
        f"Users skipped: {result['users_skipped']}"
    )

    print()
    print("Synchronization complete.")

