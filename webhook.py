from flask import Flask, request, jsonify

from sheets import get_all_records, update_record


app = Flask(__name__)


# ============================================================
# FIND NOTIFICATION BY TWILIO MESSAGE SID
# ============================================================

def find_notification_by_sid(message_sid):
    """
    Find a notification in Google Sheets using the
    Twilio Message SID.
    """

    notifications = get_all_records("Notification")

    for row in notifications:

        stored_sid = str(
            row.get("Twilio SID", "")
        ).strip()

        if stored_sid == message_sid:
            return row

    return None


# ============================================================
# TWILIO STATUS WEBHOOK
# ============================================================

@app.route("/twilio/status", methods=["POST"])
def twilio_status():

    message_sid = request.form.get(
        "MessageSid",
        ""
    ).strip()

    message_status = request.form.get(
        "MessageStatus",
        ""
    ).strip().lower()

    error_code = request.form.get(
        "ErrorCode",
        ""
    ).strip()

    error_message = request.form.get(
        "ChannelStatusMessage",
        ""
    ).strip()

    print()
    print("=" * 60)
    print("TWILIO STATUS CALLBACK")
    print("=" * 60)

    print("Message SID:", message_sid)
    print("Status:", message_status)

    if error_code:
        print("Error Code:", error_code)

    if error_message:
        print("Error:", error_message)

    # --------------------------------------------------------
    # Validate SID
    # --------------------------------------------------------

    if not message_sid:

        return jsonify({
            "success": False,
            "error": "Missing MessageSid",
        }), 400

    # --------------------------------------------------------
    # Find notification
    # --------------------------------------------------------

    notification = find_notification_by_sid(
        message_sid
    )

    if not notification:

        print(
            "WARNING: No notification found for SID:",
            message_sid,
        )

        # Return 200 to prevent unnecessary Twilio retries.
        return jsonify({
            "success": False,
            "error": "Notification not found",
        }), 200

    notification_id = notification.get(
        "Notification ID"
    )

    row_number = notification.get(
        "Row number"
    )

    print("Notification:", notification_id)

    if not row_number:

        print(
            "ERROR: Notification has no row number."
        )

        return jsonify({
            "success": False,
            "error": "Notification has no row number",
        }), 500

    # --------------------------------------------------------
    # STATUS MAPPING
    # --------------------------------------------------------

    status_mapping = {

        "queued": "Queued",

        "accepted": "Queued",

        "sending": "Sending",

        "sent": "Sent",

        "delivered": "Delivered",

        "read": "Read",

        "failed": "Failed",

        "undelivered": "Undelivered",

        "canceled": "Failed",
    }

    new_status = status_mapping.get(
        message_status,
        message_status.title(),
    )

    # --------------------------------------------------------
    # PREPARE UPDATE
    # --------------------------------------------------------

    updates = {
        "Status": new_status,
    }

    # --------------------------------------------------------
    # SUCCESSFUL DELIVERY
    # --------------------------------------------------------

    if message_status in (
        "sent",
        "delivered",
        "read",
    ):

        updates["Last Error"] = ""

        # Only set Sent At if it doesn't already exist.
        if not notification.get("Sent At"):

            from datetime import datetime

            updates["Sent At"] = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

    # --------------------------------------------------------
    # DELIVERY FAILURE
    # --------------------------------------------------------

    elif message_status in (
        "failed",
        "undelivered",
    ):

        if error_code:

            updates["Last Error"] = (
                f"Twilio {error_code}"
            )

        elif error_message:

            updates["Last Error"] = (
                error_message
            )

        else:

            updates["Last Error"] = (
                "Twilio delivery failed"
            )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Put failed notification back into Pending so the
        # existing sender retry engine can process it.
        # ----------------------------------------------------

        retry_count_raw = notification.get(
            "Retry Count",
            ""
        )

        try:

            retry_count = int(
                retry_count_raw or 0
            )

        except (
            ValueError,
            TypeError,
        ):

            retry_count = 0

        # The existing sender engine allows 3 attempts.
        if retry_count >= 3:

            updates["Status"] = (
                "Permanently Failed"
            )

            print(
                f"🚫 Notification "
                f"{notification_id} "
                f"has reached maximum retries."
            )

        else:

            updates["Status"] = "Pending"

            print(
                f"🔄 Notification "
                f"{notification_id} "
                f"returned to Pending "
                f"for retry."
            )

    # --------------------------------------------------------
    # UPDATE GOOGLE SHEETS
    # --------------------------------------------------------

    update_record(
        "Notification",
        row_number,
        updates,
    )

    print(
        f"Notification {notification_id} "
        f"updated to {updates['Status']}."
    )

    return jsonify({
        "success": True,
        "notification_id": notification_id,
        "status": updates["Status"],
    }), 200


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def health():

    return jsonify({
        "service": "Local Events Twilio Webhook",
        "status": "running",
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("LOCAL EVENTS TWILIO WEBHOOK")
    print("=" * 60)

    print()
    print("Listening on:")
    print("http://127.0.0.1:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )