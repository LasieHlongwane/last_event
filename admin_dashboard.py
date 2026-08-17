import streamlit as st
import pandas as pd
from datetime import datetime

from sheets import get_all_records
from subscription_sync import main as sync_subscriptions
from notifications import (
    create_notification,
    build_notification_key,
    notification_exists,
    get_notification_channels,
)
from sender import process_pending_notifications


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Local Events Admin",
    page_icon="📱",
    layout="wide",
)


# ============================================================
# CONSTANTS
# ============================================================

USERS_SHEET = "Users"
EVENTS_SHEET = "Events"
NOTIFICATIONS_SHEET = "Notification"
AREAS_SHEET = "Areas"


# ============================================================
# HELPERS
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize_lower(value):
    return normalize(value).lower()


def get_users():
    return get_all_records(USERS_SHEET)


def get_events():
    return get_all_records(EVENTS_SHEET)


def get_notifications():
    return get_all_records(NOTIFICATIONS_SHEET)


def get_areas():
    """
    Load the Areas master sheet.

    Expected structure:

        areavillagemain_area | village | main_area

    Example:

        Zakheni, KwaMhlanga | Zakheni | KwaMhlanga
        Leratong, KwaMhlanga | Leratong | KwaMhlanga
        SunCity, KwaMhlanga | SunCity | KwaMhlanga
        KwaMhlanga Central | Central | KwaMhlanga
    """

    return get_all_records(AREAS_SHEET)


def get_active_users(users):

    result = []

    for user in users:

        active = normalize_lower(
            user.get("active")
        )

        if active in [
            "",
            "yes",
            "true",
            "1",
            "active",
        ]:
            result.append(user)

    return result


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
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# AREA MASTER HELPERS
# ============================================================

def get_area_master_mapping(area_records):
    """
    Build mappings from the Areas master sheet.

    Returns:

        {
            "zakheni": {
                "village": "Zakheni",
                "main_area": "KwaMhlanga",
                "full_area": "Zakheni, KwaMhlanga"
            },

            ...
        }
    """

    mapping = {}

    for record in area_records:

        village = normalize(
            record.get("village")
            or record.get("Village")
            or record.get("VILLAGE")
        )

        main_area = normalize(
            record.get("main_area")
            or record.get("Main Area")
            or record.get("main area")
            or record.get("MAIN AREA")
        )

        full_area = normalize(
            record.get("areavillagemain_area")
            or record.get("AreaVillageMain_Area")
            or record.get("area_village_main_area")
            or record.get("area")
        )

        if not village and full_area:

            village = full_area.split(",")[0].strip()

        if not main_area and full_area:

            parts = [
                item.strip()
                for item in full_area.split(",")
                if item.strip()
            ]

            if len(parts) >= 2:
                main_area = parts[-1]

        if not village:
            continue

        if not main_area:
            continue

        mapping[
            normalize_lower(village)
        ] = {
            "village": village,
            "main_area": main_area,
            "full_area": full_area or village,
        }

    return mapping


def find_area_mapping(
    area_value,
    area_mapping,
):
    """
    Find an Areas master record for a user's area.

    Handles:

        Zakheni
        Zakheni, KwaMhlanga
        Leratong, KwaMhlanga
        SunCity, KwaMhlanga
        KwaMhlanga Central
    """

    area_value = normalize(area_value)

    if not area_value:
        return None

    area_lower = normalize_lower(
        area_value
    )

    # --------------------------------------------------------
    # 1. Exact full-area match
    # --------------------------------------------------------

    for item in area_mapping.values():

        if (
            normalize_lower(
                item["full_area"]
            )
            == area_lower
        ):
            return item

    # --------------------------------------------------------
    # 2. Exact village match
    # --------------------------------------------------------

    if area_lower in area_mapping:

        return area_mapping[
            area_lower
        ]

    # --------------------------------------------------------
    # 3. Extract village from:
    #
    # Zakheni, KwaMhlanga
    # --------------------------------------------------------

    first_part = area_value.split(",")[0].strip()

    first_part_lower = normalize_lower(
        first_part
    )

    if first_part_lower in area_mapping:

        return area_mapping[
            first_part_lower
        ]

    # --------------------------------------------------------
    # 4. Match main area directly
    # --------------------------------------------------------

    for item in area_mapping.values():

        if (
            normalize_lower(
                item["main_area"]
            )
            == area_lower
        ):
            return item

    return None


def get_user_area_details(
    user,
    area_mapping,
):
    """
    Convert a user's stored area into:

        village
        main_area
        full_area
    """

    raw_areas = split_values(
        user.get("areas")
    )

    results = []

    for raw_area in raw_areas:

        mapping = find_area_mapping(
            raw_area,
            area_mapping,
        )

        if mapping:

            results.append(
                mapping
            )

    return results


def get_user_main_areas(
    user,
    area_mapping,
):
    """
    Return all main areas belonging to a user.
    """

    details = get_user_area_details(
        user,
        area_mapping,
    )

    return {
        normalize_lower(
            item["main_area"]
        )
        for item in details
        if item.get("main_area")
    }


def get_user_villages(
    user,
    area_mapping,
):
    """
    Return all villages belonging to a user.
    """

    details = get_user_area_details(
        user,
        area_mapping,
    )

    return {
        normalize_lower(
            item["village"]
        )
        for item in details
        if item.get("village")
    }


def get_event_main_area(
    event,
    area_mapping,
):
    """
    Convert an event's area into its main area.

    Example:

        Event area:
            Zakheni, KwaMhlanga

        Returns:
            KwaMhlanga
    """

    event_area = normalize(
        event.get("area")
    )

    if not event_area:
        return ""

    mapping = find_area_mapping(
        event_area,
        area_mapping,
    )

    if mapping:

        return mapping[
            "main_area"
        ]

    # --------------------------------------------------------
    # If event is already stored as main area
    # --------------------------------------------------------

    for item in area_mapping.values():

        if (
            normalize_lower(
                item["main_area"]
            )
            == normalize_lower(
                event_area
            )
        ):
            return item[
                "main_area"
            ]

    return event_area


# ============================================================
# MATCHING
# ============================================================

def user_matches_event_safe(
    user,
    event,
    area_mapping,
):
    """
    Dashboard matching engine.

    Matching logic:

        MAIN AREA + CATEGORY + ACTIVE + OPT-IN

    Example:

        User:
            Zakheni, KwaMhlanga

        Event:
            Leratong, KwaMhlanga

        Main area:
            KwaMhlanga

        Result:
            MATCH

    This allows the system to treat KwaMhlanga as one
    notification region while still keeping village-level
    information for analytics.
    """

    # --------------------------------------------------------
    # ACTIVE USER
    # --------------------------------------------------------

    active = normalize_lower(
        user.get("active")
    )

    if active and active not in [
        "yes",
        "true",
        "1",
        "active",
    ]:
        return False

    # --------------------------------------------------------
    # CATEGORY MATCH
    # --------------------------------------------------------

    event_category = normalize_lower(
        event.get("category")
    )

    user_categories = {
        normalize_lower(category)
        for category in split_values(
            user.get("categories")
        )
    }

    if (
        event_category
        not in user_categories
    ):
        return False

    # --------------------------------------------------------
    # AREA MATCH
    # --------------------------------------------------------

    event_main_area = normalize_lower(
        get_event_main_area(
            event,
            area_mapping,
        )
    )

    user_main_areas = get_user_main_areas(
        user,
        area_mapping,
    )

    if not event_main_area:
        return False

    if (
        event_main_area
        not in user_main_areas
    ):
        return False

    # --------------------------------------------------------
    # NOTIFICATION CHANNEL
    # --------------------------------------------------------

    channels = get_notification_channels(
        user
    )

    if not channels:
        return False

    return True


def find_matches(
    event,
    users,
    area_mapping,
):

    matches = []

    for user in users:

        if user_matches_event_safe(
            user,
            event,
            area_mapping,
        ):

            matches.append(user)

    return matches


# ============================================================
# LABEL HELPERS
# ============================================================

def event_label(event):

    return (
        f"{event.get('event_name', 'Unnamed Event')} "
        f"| {event.get('area', '')} "
        f"| {event.get('category', '')} "
        f"| {event.get('event_date', '')}"
    )


def get_event_key(event):

    return (
        event.get(
            "event_id"
        )
        or event_label(event)
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "📱 Local Events Admin Dashboard"
)

st.caption(
    "MVP control panel — subscribers, areas, events, "
    "matching and notifications."
)


# ============================================================
# TOP CONTROLS
# ============================================================

col1, col2 = st.columns(
    [1, 5]
)

with col1:

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        st.rerun()


with col2:

    st.info(
        "Subscriber locations are managed through "
        "the Areas master sheet. Villages are grouped "
        "under their main areas for matching and reporting."
    )


# ============================================================
# LOAD DATA
# ============================================================

try:

    users = get_users()

    events = get_events()

    notifications = get_notifications()

    area_records = get_areas()

except Exception as exc:

    st.error(
        "Unable to load Google Sheets data: "
        f"{exc}"
    )

    st.stop()


# ============================================================
# BUILD AREA MASTER
# ============================================================

area_mapping = get_area_master_mapping(
    area_records
)


if not area_mapping:

    st.warning(
        """
The Areas master sheet is empty or could not be read.

Please create the Areas sheet with columns such as:

areavillagemain_area | village | main_area
"""
    )


active_users = get_active_users(
    users
)


# ============================================================
# OVERVIEW
# ============================================================

st.header(
    "📊 Audience Overview"
)

col1, col2, col3, col4 = st.columns(
    4
)

with col1:

    st.metric(
        "Total Subscribers",
        len(active_users),
    )

with col2:

    st.metric(
        "Active Subscribers",
        len(active_users),
    )

with col3:

    st.metric(
        "Events",
        len(events),
    )

with col4:

    st.metric(
        "Notifications",
        len(notifications),
    )


# ============================================================
# MAIN AREA OVERVIEW
# ============================================================

st.subheader(
    "🌍 Subscribers by Main Area"
)


main_area_counts = {}

for user in active_users:

    main_areas = get_user_main_areas(
        user,
        area_mapping,
    )

    for main_area in main_areas:

        main_area_counts[
            main_area
        ] = (
            main_area_counts.get(
                main_area,
                0,
            )
            + 1
        )


if main_area_counts:

    main_area_rows = []

    for area, count in sorted(
        main_area_counts.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        main_area_rows.append(
            {
                "Main Area": area,
                "Total Subscribers": count,
            }
        )

    main_area_df = pd.DataFrame(
        main_area_rows
    )

    st.dataframe(
        main_area_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No main-area subscriber data available."
    )


# ============================================================
# SELECTED MAIN AREA
# ============================================================

st.subheader(
    "📍 Area Subscriber Breakdown"
)


if main_area_counts:

    selected_main_area = st.selectbox(
        "Select main area",
        sorted(
            main_area_counts.keys()
        ),
        key="dashboard_main_area",
    )

    selected_area_users = []

    for user in active_users:

        user_main_areas = (
            get_user_main_areas(
                user,
                area_mapping,
            )
        )

        if (
            normalize_lower(
                selected_main_area
            )
            in user_main_areas
        ):

            selected_area_users.append(
                user
            )

    st.metric(
        f"{selected_main_area} — Total Subscribers",
        len(selected_area_users),
    )

    # --------------------------------------------------------
    # VILLAGE COUNTS
    # --------------------------------------------------------

    village_counts = {}

    for user in selected_area_users:

        villages = get_user_villages(
            user,
            area_mapping,
        )

        for village in villages:

            # Make sure this village belongs
            # to the selected main area.
            mapping = area_mapping.get(
                village
            )

            if not mapping:
                continue

            if (
                normalize_lower(
                    mapping["main_area"]
                )
                != normalize_lower(
                    selected_main_area
                )
            ):
                continue

            display_village = (
                mapping["village"]
            )

            village_counts[
                display_village
            ] = (
                village_counts.get(
                    display_village,
                    0,
                )
                + 1
            )

    if village_counts:

        village_rows = []

        for village, count in sorted(
            village_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        ):

            village_rows.append(
                {
                    "Village": village,
                    "Users": count,
                }
            )

        village_df = pd.DataFrame(
            village_rows
        )

        st.dataframe(
            village_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No village-level subscriber data "
            "available for this main area."
        )


# ============================================================
# CATEGORY STATISTICS
# ============================================================

st.subheader(
    "🎯 Subscribers by Category"
)

category_counts = {}

for user in active_users:

    categories = split_values(
        user.get("categories")
    )

    for category in categories:

        category = normalize(
            category
        )

        if not category:
            continue

        category_counts[
            category
        ] = (
            category_counts.get(
                category,
                0,
            )
            + 1
        )


if category_counts:

    category_df = pd.DataFrame(
        [
            {
                "Category": category,
                "Subscribers": count,
            }
            for category, count
            in sorted(
                category_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]
    )

    st.dataframe(
        category_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No subscriber category data available."
    )


# ============================================================
# AREA MASTER
# ============================================================

st.divider()

st.header(
    "🗺️ Area Master"
)

st.caption(
    "The Areas sheet controls how villages are grouped "
    "into main notification areas."
)

if area_records:

    area_master_rows = []

    for record in area_records:

        mapping = find_area_mapping(
            normalize(
                record.get(
                    "village"
                )
                or record.get(
                    "Village"
                )
            ),
            area_mapping,
        )

        if mapping:

            area_master_rows.append(
                {
                    "Village":
                        mapping["village"],

                    "Main Area":
                        mapping["main_area"],

                    "Full Area":
                        mapping["full_area"],
                }
            )

    if area_master_rows:

        area_master_df = pd.DataFrame(
            area_master_rows
        )

        st.dataframe(
            area_master_df,
            use_container_width=True,
            hide_index=True,
        )

else:

    st.info(
        "No Areas master records found."
    )


# ============================================================
# SUBSCRIBER SYNCHRONIZATION
# ============================================================

st.divider()

st.header(
    "👤 Subscriber Management"
)

st.write(
    "When someone submits the registration form, "
    "their response appears in the registration "
    "responses sheet."
)

st.write(
    "Click the button below to synchronize those "
    "registrations into the Users sheet."
)


if st.button(
    "🔄 Sync New Subscribers",
    type="primary",
    use_container_width=True,
):

    with st.spinner(
        "Synchronizing subscribers..."
    ):

        try:

            sync_subscriptions()

            st.success(
                "Subscriber synchronization completed."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                "Subscriber synchronization failed: "
                f"{exc}"
            )


# ============================================================
# EVENT NOTIFICATION CENTER
# ============================================================

st.divider()

st.header(
    "📢 Event Notification Center"
)

st.write(
    "Select an event, preview the matching audience, "
    "then manually send the notifications."
)


# ============================================================
# AVAILABLE EVENTS
# ============================================================

if not events:

    st.warning(
        "No events available."
    )

else:

    active_events = [

        event

        for event in events

        if normalize_lower(
            event.get("status")
        ) == "active"

    ]

    if not active_events:

        st.info(
            "There are currently no active events."
        )

    else:

        event_options = {
            event_label(event): event
            for event in active_events
        }

        selected_label = st.selectbox(
            "Select Event",
            list(
                event_options.keys()
            ),
        )

        selected_event = event_options[
            selected_label
        ]

        # ====================================================
        # EVENT DETAILS
        # ====================================================

        st.subheader(
            "📋 Event Details"
        )

        col1, col2, col3 = st.columns(
            3
        )

        with col1:

            st.write(
                "**Event**"
            )

            st.write(
                selected_event.get(
                    "event_name"
                )
            )

        with col2:

            st.write(
                "**Area**"
            )

            st.write(
                selected_event.get(
                    "area"
                )
            )

        with col3:

            st.write(
                "**Main Area**"
            )

            st.write(
                get_event_main_area(
                    selected_event,
                    area_mapping,
                )
            )

        col1, col2, col3 = st.columns(
            3
        )

        with col1:

            st.write(
                "**Category**"
            )

            st.write(
                selected_event.get(
                    "category"
                )
            )

        with col2:

            st.write(
                "**Date**"
            )

            st.write(
                selected_event.get(
                    "event_date"
                )
            )

        with col3:

            st.write(
                "**Time**"
            )

            st.write(
                selected_event.get(
                    "event_time"
                )
            )

        st.write(
            "**Venue**"
        )

        st.write(
            selected_event.get(
                "venue"
            )
        )

        # ====================================================
        # FIND MATCHES
        # ====================================================

        st.subheader(
            "🔎 Audience Matching"
        )

        if st.button(
            "🔎 Find Matching Users",
            use_container_width=True,
        ):

            matches = find_matches(
                selected_event,
                active_users,
                area_mapping,
            )

            st.session_state[
                "matched_users"
            ] = matches

            st.session_state[
                "matched_event_key"
            ] = get_event_key(
                selected_event
            )

        # ====================================================
        # DISPLAY MATCHES
        # ====================================================

        matched_users = (
            st.session_state.get(
                "matched_users",
                [],
            )
        )

        matched_event_key = (
            st.session_state.get(
                "matched_event_key"
            )
        )

        current_event_key = (
            get_event_key(
                selected_event
            )
        )

        if (
            matched_event_key
            == current_event_key
        ):

            st.write(
                f"### Matching Users: "
                f"{len(matched_users)}"
            )

            if matched_users:

                match_rows = []

                for user in matched_users:

                    user_details = (
                        get_user_area_details(
                            user,
                            area_mapping,
                        )
                    )

                    villages = ", ".join(
                        sorted(
                            {
                                item["village"]
                                for item
                                in user_details
                            }
                        )
                    )

                    main_areas = ", ".join(
                        sorted(
                            {
                                item["main_area"]
                                for item
                                in user_details
                            }
                        )
                    )

                    match_rows.append(
                        {
                            "User ID":
                                user.get(
                                    "user_id"
                                ),

                            "Name":
                                user.get(
                                    "name"
                                ),

                            "Phone":
                                user.get(
                                    "phone"
                                ),

                            "Village":
                                villages,

                            "Main Area":
                                main_areas,

                            "Categories":
                                user.get(
                                    "categories"
                                ),

                            "Channel":
                                user.get(
                                    "notification_channel"
                                ),

                            "WhatsApp Opt-In":
                                user.get(
                                    "whatsapp_opt_in"
                                ),

                            "SMS Opt-In":
                                user.get(
                                    "sms_opt_in"
                                ),
                        }
                    )

                match_df = pd.DataFrame(
                    match_rows
                )

                st.dataframe(
                    match_df,
                    use_container_width=True,
                    hide_index=True,
                )

                # =================================================
                # SEND PREVIEW
                # =================================================

                st.subheader(
                    "📱 Notification Preview"
                )

                st.info(
                    f"{len(matched_users)} "
                    "subscriber(s) match this event."
                )

                preview_message = (
                    "🎉 Event Alert!\n\n"
                    f"{normalize(selected_event.get('event_name'))}\n"
                    f"Date: {normalize(selected_event.get('event_date'))}\n"
                    f"Time: {normalize(selected_event.get('event_time'))}\n"
                    f"Venue: {normalize(selected_event.get('venue'))}\n"
                    f"Area: {normalize(selected_event.get('area'))}\n\n"
                    "More details coming soon."
                )

                st.text_area(
                    "Notification message",
                    preview_message,
                    height=180,
                    disabled=True,
                )

                # =================================================
                # SEND BUTTON
                # =================================================

                st.subheader(
                    "🚀 Send Notifications"
                )

                st.warning(
                    "This will create and send notifications "
                    "using each subscriber's selected channel: "
                    "WhatsApp, SMS, or Both."
                )

                confirmation = st.checkbox(
                    "I have reviewed the matching users "
                    "and want to send these notifications."
                )

                if st.button(
                    "📱 SEND NOTIFICATIONS",
                    type="primary",
                    disabled=not confirmation,
                    use_container_width=True,
                ):

                    created = 0
                    duplicates = 0
                    errors = 0

                    existing_notifications = (
                        get_notifications()
                    )

                    progress = st.progress(
                        0
                    )

                    status_box = st.empty()

                    total_users = len(
                        matched_users
                    )

                    for index, user in enumerate(
                        matched_users
                    ):

                        try:

                            channels = (
                                get_notification_channels(
                                    user
                                )
                            )

                            if not channels:

                                errors += 1

                                st.warning(
                                    f"{user.get('name')} "
                                    "has no valid opted-in "
                                    "notification channel."
                                )

                                continue

                            for channel in channels:

                                notification_key = (
                                    build_notification_key(
                                        selected_event,
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

                                create_notification(
                                    selected_event,
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

                        except Exception as exc:

                            errors += 1

                            st.error(
                                f"Failed for "
                                f"{user.get('name')}: "
                                f"{exc}"
                            )

                        progress.progress(
                            (index + 1)
                            / total_users
                        )

                    status_box.success(
                        "Notification records prepared."
                    )

                    st.write(
                        "### Notification Summary"
                    )

                    col1, col2, col3 = st.columns(
                        3
                    )

                    with col1:

                        st.metric(
                            "Created",
                            created,
                        )

                    with col2:

                        st.metric(
                            "Duplicates Blocked",
                            duplicates,
                        )

                    with col3:

                        st.metric(
                            "Errors",
                            errors,
                        )

                    # =============================================
                    # ACTUAL SENDING
                    # =============================================

                    if created > 0:

                        st.info(
                            "Sending pending notifications..."
                        )

                        try:

                            process_pending_notifications()

                            st.success(
                                "Notification processing completed."
                            )

                        except Exception as exc:

                            st.error(
                                "Notification sending failed: "
                                f"{exc}"
                            )

                    else:

                        st.info(
                            "No new notifications needed to be sent."
                        )

                    st.session_state.pop(
                        "matched_users",
                        None,
                    )

                    st.session_state.pop(
                        "matched_event_key",
                        None,
                    )

                    st.rerun()

            else:

                st.warning(
                    "No subscribers match this event."
                )

                st.write(
                    "Check the event's area, category "
                    "and the Areas master sheet."
                )


# ============================================================
# NOTIFICATION HISTORY
# ============================================================

st.divider()

st.header(
    "📨 Notification History"
)

notifications = get_notifications()

if notifications:

    history_rows = []

    for notification in reversed(
        notifications[-50:]
    ):

        history_rows.append(
            {
                "Notification ID":
                    notification.get(
                        "Notification ID"
                    ),

                "Event":
                    notification.get(
                        "Event Name"
                    ),

                "User":
                    notification.get(
                        "User Name"
                    ),

                "Phone":
                    notification.get(
                        "Phone Number"
                    ),

                "Channel":
                    notification.get(
                        "Notification Channel"
                    ),

                "Status":
                    notification.get(
                        "Status"
                    ),

                "Created":
                    notification.get(
                        "Created At"
                    ),

                "Sent":
                    notification.get(
                        "Sent At"
                    ),
            }
        )

    history_df = pd.DataFrame(
        history_rows
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No notifications yet."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Local Events Notification MVP • "
    f"Dashboard refreshed: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)