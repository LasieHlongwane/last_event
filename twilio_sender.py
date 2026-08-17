import os

from twilio.rest import Client


# ============================================================
# STATUS CALLBACK
# ============================================================

STATUS_CALLBACK_URL = os.getenv(
    "TWILIO_STATUS_CALLBACK_URL",
    "",
).strip()


# ============================================================
# CONFIGURATION
# ============================================================

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_WHATSAPP_FROM = os.getenv(
    "TWILIO_WHATSAPP_FROM"
)

TWILIO_SMS_FROM = os.getenv(
    "TWILIO_SMS_FROM"
)


# ============================================================
# VALIDATION
# ============================================================

def validate_base_config():

    missing = []

    if not TWILIO_ACCOUNT_SID:

        missing.append(
            "TWILIO_ACCOUNT_SID"
        )

    if not TWILIO_AUTH_TOKEN:

        missing.append(
            "TWILIO_AUTH_TOKEN"
        )

    if missing:

        raise RuntimeError(
            "Missing Twilio configuration: "
            + ", ".join(missing)
        )


def validate_whatsapp_config():

    validate_base_config()

    if not TWILIO_WHATSAPP_FROM:

        raise RuntimeError(
            "TWILIO_WHATSAPP_FROM "
            "is not configured."
        )


def validate_sms_config():

    validate_base_config()

    if not TWILIO_SMS_FROM:

        raise RuntimeError(
            "TWILIO_SMS_FROM "
            "is not configured."
        )


# ============================================================
# PHONE NORMALIZATION
# ============================================================

def normalize_phone(phone):

    if phone is None:

        raise ValueError(
            "Phone number is empty."
        )

    phone = str(phone).strip()

    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if phone.startswith("+"):

        return phone

    if phone.startswith("27"):

        return "+" + phone

    if phone.startswith("0"):

        return (
            "+27"
            + phone[1:]
        )

    return (
        "+27"
        + phone
    )


# ============================================================
# TWILIO CLIENT
# ============================================================

def get_twilio_client():

    validate_base_config()

    return Client(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
    )


# ============================================================
# CALLBACK
# ============================================================

def callback_kwargs():

    if STATUS_CALLBACK_URL:

        return {
            "status_callback":
                STATUS_CALLBACK_URL
        }

    return {}


# ============================================================
# WHATSAPP
# ============================================================

def send_whatsapp(
    phone_number,
    message,
):

    validate_whatsapp_config()

    phone = normalize_phone(
        phone_number
    )

    from_number = (
        TWILIO_WHATSAPP_FROM
    )

    if not from_number.startswith(
        "whatsapp:"
    ):

        from_number = (
            "whatsapp:"
            + from_number
        )

    to_number = (
        "whatsapp:"
        + phone
    )

    print()
    print(
        "TWILIO WHATSAPP SEND"
    )

    print(
        "To:",
        to_number
    )

    client = get_twilio_client()

    kwargs = callback_kwargs()

    message = client.messages.create(
        from_=from_number,
        to=to_number,
        body=message,
        **kwargs,
    )

    print(
        "Twilio SID:",
        message.sid
    )

    print(
        "Twilio status:",
        message.status
    )

    return {

        "success":
            True,

        "message_sid":
            message.sid,

        "status":
            message.status,
    }


# ============================================================
# SMS
# ============================================================

def send_sms(
    phone_number,
    message,
):

    validate_sms_config()

    phone = normalize_phone(
        phone_number
    )

    from_number = (
        TWILIO_SMS_FROM
    )

    if from_number.startswith(
        "whatsapp:"
    ):

        from_number = (
            from_number[
                len("whatsapp:"):
            ]
        )

    if not from_number.startswith("+"):

        from_number = normalize_phone(
            from_number
        )

    print()
    print(
        "TWILIO SMS SEND"
    )

    print(
        "To:",
        phone
    )

    client = get_twilio_client()

    kwargs = callback_kwargs()

    message = client.messages.create(
        from_=from_number,
        to=phone,
        body=message,
        **kwargs,
    )

    print(
        "Twilio SID:",
        message.sid
    )

    print(
        "Twilio status:",
        message.status
    )

    return {

        "success":
            True,

        "message_sid":
            message.sid,

        "status":
            message.status,
    }


# ============================================================
# GENERIC SEND
# ============================================================

def send_message(
    channel,
    phone_number,
    message,
):

    channel = str(
        channel
    ).strip().lower()

    if channel == "whatsapp":

        return send_whatsapp(
            phone_number,
            message,
        )

    if channel == "sms":

        return send_sms(
            phone_number,
            message,
        )

    raise ValueError(
        f"Unsupported notification channel: {channel}"
    )