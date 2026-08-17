from datetime import datetime
from sheets import get_all_records, update_record, get_headers


USERS_SHEET = "Users"
RESPONSES_SHEET = "Form Responses 5"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(value):
    """
    Convert phone numbers into a consistent comparison format.

    Examples:

        0761234567
        2761234567
        +27761234567

    become comparable.
    """

    if value is None:
        return ""

    value = str(value).strip()

    # Remove spaces and common formatting characters
    value = (
        value
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # Remove leading +
    if value.startswith("+"):
        value = value[1:]

    # South African local number
    if value.startswith("0") and len(value) == 10:
        value = "27" + value[1:]

    return value


# ============================================================
# LIST NORMALIZATION
# ============================================================

def normalize_list(value):
    """
    Convert:

        Music, Sports
        Music | Sports
        Music; Sports

    into:

        Music, Sports
    """

    if not value:
        return ""

    value = str(value)

    for separator in ["|", ";"]:
        value = value.replace(separator, ",")

    items = []

    for item in value.split(","):

        item = item.strip()

        if item and item not in items:
            items.append(item)

    return ", ".join(items)


# ============================================================
# FIND USER BY PHONE
# ============================================================

def find_user_by_phone(phone):

    target_phone = normalize_phone(phone)

    if not target_phone:
        return None

    users = get_all_records(
        USERS_SHEET
    )

    for user in users:

        user_phone = normalize_phone(
            user.get("phone")
        )

        if user_phone == target_phone:
            return user

    return None


# ============================================================
# PROCESS SUBSCRIPTION RESPONSE
# ============================================================

def process_subscription(response):

    phone = response.get(
        "Phone Number"
    )

    name = response.get(
        "Name"
    )

    areas = normalize_list(
        response.get("Areas")
    )

    categories = normalize_list(
        response.get("Categories")
    )

    channel = str(
        response.get(
            "Notification Channel"
        ) or ""
    ).strip()

    whatsapp_opt_in = str(
        response.get(
            "WhatsApp Opt-In"
        ) or ""
    ).strip()

    action = normalize(
        response.get(
            "Subscription Action"
        )
    )

    print()
    print("=" * 60)
    print("PROCESSING SUBSCRIPTION")
    print("=" * 60)

    print("Name:", name)
    print("Phone:", phone)
    print("Areas:", areas)
    print("Categories:", categories)
    print("Channel:", channel)
    print("WhatsApp Opt-In:", whatsapp_opt_in)
    print("Action:", action)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not normalize_phone(phone):

        print()
        print("ERROR: Missing phone number.")
        return False

    # --------------------------------------------------------
    # FIND EXISTING USER
    # --------------------------------------------------------

    user = find_user_by_phone(
        phone
    )

    # ========================================================
    # UNSUBSCRIBE
    # ========================================================

    if action == "unsubscribe":

        if not user:

            print()
            print(
                "WARNING: User not found."
            )

            return False

        row_number = user.get(
            "Row number"
        )

        if not row_number:

            print(
                "ERROR: User has no row number."
            )

            return False

        update_record(
            USERS_SHEET,
            row_number,
            {
                "active": "No",
                "whatsapp_opt_in": "No",
            },
        )

        print()
        print(
            f"User {user.get('name')} "
            "successfully unsubscribed."
        )

        return True

    # ========================================================
    # UPDATE EXISTING USER
    # ========================================================

    if user:

        row_number = user.get(
            "Row number"
        )

        if not row_number:

            print(
                "ERROR: User has no row number."
            )

            return False

        updates = {
            "name": name,
            "phone": phone,
            "area": areas,
            "categories": categories,
            "notification_channel": channel,
            "active": "Yes",
            "whatsapp_opt_in": whatsapp_opt_in,
        }

        update_record(
            USERS_SHEET,
            row_number,
            updates,
        )

        print()
        print(
            f"User {user.get('name')} "
            "subscription updated."
        )

        return True

    # ========================================================
    # NEW USER
    # ========================================================

    print()
    print(
        "User does not exist."
    )

    print(
        "Creating a new user..."
    )

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    # Your current sheets.py should already contain whatever
    # function you use to create records.
    #
    # We will connect this part after checking the available
    # create/append function in sheets.py.
    # --------------------------------------------------------

    print()
    print(
        "NEW USER CREATION NOT YET CONNECTED."
    )

    print(
        "Existing-user update and unsubscribe "
        "logic are ready."
    )

    return False


# ============================================================
# FIND NEW RESPONSES
# ============================================================

def process_pending_responses():

    responses = get_all_records(
        RESPONSES_SHEET
    )

    if not responses:

        print(
            "No subscription responses found."
        )

        return

    print()
    print(
        f"Subscription responses: "
        f"{len(responses)}"
    )

    # For the first production version we process
    # the latest response.
    response = responses[-1]

    process_subscription(
        response
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("LOCAL EVENTS SUBSCRIPTION MANAGER")
    print("=" * 60)

    process_pending_responses()

    print()
    print(
        "Subscription processing complete."
    )


if __name__ == "__main__":
    main()