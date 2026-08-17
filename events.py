
import uuid
from datetime import datetime

from sheets import get_all_records, append_record


SOURCE_SHEET = "Form Responses 3"
TARGET_SHEET = "Events"


def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def generate_event_id():
    return "EVT-" + uuid.uuid4().hex[:10].upper()


def synchronize_events():

    print("=" * 60)
    print("EVENT SYNCHRONIZATION")
    print("=" * 60)

    source_rows = get_all_records(SOURCE_SHEET)
    existing_events = get_all_records(TARGET_SHEET)

    existing_event_names = {
        normalize(event.get("event_name")).lower()
        for event in existing_events
        if event.get("event_name")
    }

    added = 0
    skipped = 0

    for row in source_rows:

        event_name = normalize(
            row.get("Event Name")
        )

        if not event_name:
            skipped += 1
            continue

        # Prevent duplicate events.
        if event_name.lower() in existing_event_names:
            skipped += 1
            continue

        event = {
            "event_id": generate_event_id(),

            "event_name": event_name,

            "description": normalize(
                row.get("Description")
            ),

            "event_date": normalize(
                row.get("Event Date")
            ),

            "event_time": normalize(
                row.get("Start time")
            ),

            "venue": normalize(
                row.get("Venue")
            ),

            "area": normalize(
                row.get("Area")
            ),

            "category": normalize(
                row.get("Category")
            ),

            "ticket_price": normalize(
                row.get("Ticket price")
            ),

            "contact": normalize(
                row.get("Contact Number")
            ),

            "social_link": normalize(
                row.get("Social Media Link")
            ),

            "poster_url": normalize(
                row.get("Event Poster(Image)")
            ),

            "status": "Active",

            "notification_status": "Pending",

            "created_at": datetime.now().isoformat(),
        }

        append_record(
            TARGET_SHEET,
            event
        )

        existing_event_names.add(
            event_name.lower()
        )

        added += 1

        print(
            f"ADDED: {event_name} "
            f"| {event['area']} "
            f"| {event['category']}"
        )

    print()
    print(f"Events added: {added}")
    print(f"Events skipped: {skipped}")
    print()
    print("Synchronization complete.")


if __name__ == "__main__":
    synchronize_events()

