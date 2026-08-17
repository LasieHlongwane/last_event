"""
MAIN AUTOMATION CONTROLLER

Complete Local Events notification pipeline:

1. Synchronize users from form responses
2. Synchronize events
3. Match events to subscribed users
4. Create notifications
5. Send pending notifications

Run:

    python run.py
"""

from datetime import datetime
import traceback

from users import sync_users
from events import synchronize_events
from notifications import main as create_notifications
from sender import process_pending_notifications


def print_section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def run_pipeline():

    start_time = datetime.now()

    print("=" * 60)
    print("LOCAL EVENTS NOTIFICATION AUTOMATION")
    print("=" * 60)

    print()
    print(
        "Started:",
        start_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    # =========================================================
    # STEP 1 — USER SYNCHRONIZATION
    # =========================================================

    print_section(
        "STEP 1 — USER SYNCHRONIZATION"
    )

    try:

        sync_users()

    except Exception as e:

        print()
        print(
            "ERROR during user synchronization:"
        )

        print(e)
        traceback.print_exc()

        return False

    # =========================================================
    # STEP 2 — EVENT SYNCHRONIZATION
    # =========================================================

    print_section(
        "STEP 2 — EVENT SYNCHRONIZATION"
    )

    try:

        synchronize_events()

    except Exception as e:

        print()
        print(
            "ERROR during event synchronization:"
        )

        print(e)
        traceback.print_exc()

        return False

    # =========================================================
    # STEP 3 — MATCHING + NOTIFICATION CREATION
    # =========================================================

    print_section(
        "STEP 3 — MATCH EVENTS TO USERS"
    )

    try:

        create_notifications()

    except Exception as e:

        print()
        print(
            "ERROR during notification creation:"
        )

        print(e)
        traceback.print_exc()

        return False

    # =========================================================
    # STEP 4 — SEND NOTIFICATIONS
    # =========================================================

    print_section(
        "STEP 4 — SEND PENDING NOTIFICATIONS"
    )

    try:

        process_pending_notifications()

    except Exception as e:

        print()
        print(
            "ERROR during notification sending:"
        )

        print(e)
        traceback.print_exc()

        return False

    # =========================================================
    # COMPLETE
    # =========================================================

    end_time = datetime.now()

    duration = end_time - start_time

    print()
    print("=" * 60)
    print("AUTOMATION COMPLETE")
    print("=" * 60)

    print()

    print(
        "Started:",
        start_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Finished:",
        end_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Duration:",
        duration
    )

    print()

    print(
        "Pipeline completed successfully."
    )

    return True


if __name__ == "__main__":

    success = run_pipeline()

    if not success:

        print()
        print(
            "Pipeline FAILED."
        )

        raise SystemExit(1)

    print()
    print(
        "Pipeline finished successfully."
    )