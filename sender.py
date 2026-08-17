from datetime import datetime, timezone

from twilio_sender import send_message

from sheets import (
    get_all_records,
    update_record,
)


MAX_RETRIES = 3

NOTIFICATIONS_SHEET = "Notification"


# ============================================================
# HELPERS
# ============================================================

def get_value(
    notification,
    key,
    default="",
):

    value = notification.get(
        key,
        default,
    )

    if value is None:

        return default

    return value


def get_retry_count(
    notification,
):

    value = get_value(
        notification,
        "Retry Count",
        0,
    )

    try:

        return int(value)

    except (
        TypeError,
        ValueError,
    ):

        return 0


def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# PROCESS ONE NOTIFICATION
# ============================================================

def process_notification(
    notification,
):

    notification_id = get_value(
        notification,
        "Notification ID",
    )

    row_number = get_value(
        notification,
        "Row number",
    )

    if not row_number:

        print(
            f"ERROR: Notification "
            f"{notification_id} has no row number."
        )

        return False

    try:

        row_number = int(
            row_number
        )

    except (
        ValueError,
        TypeError,
    ):

        print(
            f"ERROR: Invalid row number "
            f"for {notification_id}: "
            f"{row_number}"
        )

        return False

    try:

        # ----------------------------------------------------
        # MARK PROCESSING
        # ----------------------------------------------------

        update_record(
            NOTIFICATIONS_SHEET,
            row_number,
            {
                "Status":
                    "Processing",
            },
        )

        print()
        print(
            "=" * 60
        )

        print(
            f"Processing: "
            f"{notification_id}"
        )

        channel = normalize_channel(
            get_value(
                notification,
                "Notification Channel",
            )
        )

        phone = get_value(
            notification,
            "Phone Number",
        )

        message = get_value(
            notification,
            "Message",
        )

        print(
            "Channel:",
            channel,
        )

        print(
            "Phone:",
            phone,
        )

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        result = send_message(
            channel,
            phone,
            message,
        )

        if not result.get(
            "success"
        ):

            raise RuntimeError(
                result.get(
                    "error",
                    "Twilio send failed.",
                )
            )

        twilio_sid = result.get(
            "message_sid"
        )

        if not twilio_sid:

            raise RuntimeError(
                "Twilio accepted the "
                "message but no SID "
                "was returned."
            )

        twilio_status = result.get(
            "status",
            "queued",
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        update_record(
            NOTIFICATIONS_SHEET,
            row_number,
            {

                "Status":
                    "Queued",

                "Twilio SID":
                    twilio_sid,

                "Last Error":
                    "",

                "Sent At":
                    now(),

                "Processed At":
                    now(),
            },
        )

        print(
            f"SUCCESS: "
            f"{notification_id}"
        )

        print(
            "Channel:",
            channel,
        )

        print(
            "Twilio SID:",
            twilio_sid,
        )

        return True

    except Exception as exc:

        error_message = str(
            exc
        )

        retry_count = (
            get_retry_count(
                notification
            )
            + 1
        )

        print()
        print(
            f"ERROR sending "
            f"{notification_id}"
        )

        print(
            error_message
        )

        # ----------------------------------------------------
        # PERMANENT FAILURE
        # ----------------------------------------------------

        if retry_count >= MAX_RETRIES:

            update_record(
                NOTIFICATIONS_SHEET,
                row_number,
                {

                    "Status":
                        "Permanently Failed",

                    "Retry Count":
                        retry_count,

                    "Last Error":
                        error_message,

                    "Processed At":
                        now(),
                },
            )

            print(
                "PERMANENT FAILURE"
            )

        # ----------------------------------------------------
        # RETRY
        # ----------------------------------------------------

        else:

            update_record(
                NOTIFICATIONS_SHEET,
                row_number,
                {

                    "Status":
                        "Failed",

                    "Retry Count":
                        retry_count,

                    "Last Error":
                        error_message,
                },
            )

            print(
                f"Retry available: "
                f"{retry_count}/"
                f"{MAX_RETRIES}"
            )

        return False


# ============================================================
# CHANNEL NORMALIZATION
# ============================================================

def normalize_channel(
    channel,
):

    channel = str(
        channel
    ).strip().lower()

    if channel == "whatsapp":

        return "WhatsApp"

    if channel == "sms":

        return "SMS"

    raise ValueError(
        f"Unsupported channel: "
        f"{channel}"
    )


# ============================================================
# RECOVER STUCK
# ============================================================

def recover_stuck_notifications(
    notifications,
):

    recovered = 0

    for notification in notifications:

        status = str(
            get_value(
                notification,
                "Status",
            )
        ).strip().lower()

        row_number = get_value(
            notification,
            "Row number",
        )

        notification_id = get_value(
            notification,
            "Notification ID",
        )

        if (
            status == "processing"
            and row_number
        ):

            update_record(
                NOTIFICATIONS_SHEET,
                int(row_number),
                {

                    "Status":
                        "Pending",

                    "Last Error":
                        (
                            "Recovered from "
                            "interrupted processing."
                        ),
                },
            )

            print(
                f"Recovered: "
                f"{notification_id}"
            )

            recovered += 1

    return recovered


# ============================================================
# PROCESS PENDING
# ============================================================

def process_pending_notifications():

    notifications = get_all_records(
        NOTIFICATIONS_SHEET
    )

    recovered = (
        recover_stuck_notifications(
            notifications
        )
    )

    if recovered:

        print(
            f"Recovered: "
            f"{recovered}"
        )

        notifications = get_all_records(
            NOTIFICATIONS_SHEET
        )

    pending = []

    for notification in notifications:

        status = str(
            get_value(
                notification,
                "Status",
            )
        ).strip().lower()

        retry_count = (
            get_retry_count(
                notification
            )
        )

        if status == "pending":

            pending.append(
                notification
            )

        elif (
            status == "failed"
            and retry_count < MAX_RETRIES
        ):

            pending.append(
                notification
            )

    print()
    print(
        f"Pending notifications: "
        f"{len(pending)}"
    )

    sent = 0
    failed = 0

    for notification in pending:

        result = process_notification(
            notification
        )

        if result:

            sent += 1

        else:

            failed += 1

    print()
    print(
        "=" * 60
    )

    print(
        f"Sent:   {sent}"
    )

    print(
        f"Failed: {failed}"
    )

    return {
        "sent": sent,
        "failed": failed,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    return process_pending_notifications()


if __name__ == "__main__":

    main()