import streamlit as st
from datetime import date, datetime
import uuid

from sheets import append_record


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Local Event & Promotion Submission",
    page_icon="📢",
    layout="centered",
)


# ============================================================
# CONSTANTS
# ============================================================

EVENTS_SHEET = "Events"


# ============================================================
# AREA OPTIONS
# ============================================================

AREA_OPTIONS = [
    "All, KwaMhlanga",
    "All, Moloto",
    "All, Tweefontein",
    "All, Vlaklaagte",
    "All, Kwaggafontein",
    "All, Siyabuswa",
    "Empumelelweni, KwaMhlanga",
    "Lethuli, KwaMhlanga",
    "Leratong, KwaMhlanga",
    "Mandela, KwaMhlanga",
    "MountainView, KwaMhlanga",
    "Msholozi, KwaMhlanga",
    "Phola, KwaMhlanga",
    "Section ABC, KwaMhlanga",
    "Sheldon, KwaMhlanga",
    "Suncity, KwaMhlanga",
    "Thembalethu, KwaMhlanga",
    "Vezubuhle, KwaMhlanga",
    "Zakheni, KwaMhlanga",
    "Block 1-23, Moloto",
    "Mafishane, Moloto",
    "E, Tweefontein",
    "F, Tweefontein",
    "G, Tweefontein",
    "H, Tweefontein",
    "J, Tweefontein",
    "K, Tweefontein",
    "Thokoza, Tweefontein",
    "Phumula",
    "Number 1, Vlaklaagte",
    "Number 2, Vlaklaagte",
    "Mabhoko, Kwaggafontein",
    "A, Kwaggafontein",
    "B, Kwaggafontein",
    "C, Kwaggafontein",
    "D, Kwaggafontein",
    "A, Siyabuswa",
    "B, Siyabuswa",
    "C, Siyabuswa",
    "D, Siyabuswa",
    "Other",
]


# ============================================================
# CATEGORY OPTIONS
# ============================================================

CATEGORY_OPTIONS = [
    "Music (Events)",
    "Grocery Store Discounts",
    "Hardware Store Discounts",
    "Restaurant Deals",
    "Kasi Fast Food Deals",
    "Beauty Deals", 
    "Sales Property (Room Rentals Included)",
    "Community Meetings",
    "Sports",
    "Spirituality & Tradition( Isikhethu / Amadlozi )",  
]



# ============================================================
# HELPERS
# ============================================================

def generate_event_id():
    return "EVT-" + uuid.uuid4().hex[:8].upper()


def clean(value):
    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# HEADER
# ============================================================

st.title("📢 AWE! Submit an Event or Local Promotion")

st.write(
    "Submit your event, special offer, discount, sale "
    "or local promotion."
)

st.caption(
    "Your submission will be reviewed and can then be sent "
    "to subscribers who match the selected area and category."
)


# ============================================================
# BUSINESS / ORGANIZER
# ============================================================

st.subheader("🏪 Business / Organizer")


with st.form("event_submission_details"):

    organizer_name = st.text_input(
        "Name *",
        placeholder="e.g. X Pub & Grills / X Supermarket",
    )

    contact = st.text_input(
        "Phone Number *",
        placeholder="e.g. 0761234567",
    )

    st.divider()

    # ========================================================
    # EVENT / PROMOTION
    # ========================================================

    st.subheader("📢 Event / Promotion")

    event_name = st.text_input(
        "Event / Promotion Name *",
        placeholder="e.g. X's Birthday Celebration / Weekend Grocery Special",
    )

    description = st.text_area(
        "Description *",
        placeholder=(
            "Describe the event, special offer, discount "
            "or promotion."
        ),
        height=120,
    )

    category = st.selectbox(
        "Category *",
        CATEGORY_OPTIONS,
    )

    venue = st.text_input(
        "Venue / Location",
        placeholder="e.g. KwaMhlanga Stadium",
    )

    st.divider()

    # ========================================================
    # LOCATION
    # ========================================================

    st.subheader(
        "📍 Promotion / Event Location"
    )

    selected_areas = st.multiselect(
        "Area *",
        AREA_OPTIONS,
        placeholder="Select one or more areas...",
        key="event_areas",
    )

    # ========================================================
    # OTHER AREA
    # ========================================================

    other_area = ""

    if "Other" in selected_areas:

        other_area = st.text_input(
            "Enter your area *",
            placeholder="e.g. Mmametlhake, KwaMhlanga",
            key="event_other_area",
            help=(
                "Enter the name of your village, section, "
                "complex or area."
            ),
        )

    # ========================================================
    # FINAL AREA LIST
    # ========================================================

    final_areas = [
        area.strip()
        for area in selected_areas
        if area != "Other"
        and area.strip()
    ]

    if other_area.strip():

        final_areas.append(
            other_area.strip()
        )

    st.divider()

    # ========================================================
    # OPTIONAL INFORMATION
    # ========================================================

    st.subheader(
        "💰 Optional Information"
    )

    ticket_price = st.text_input(
        "Price / Special Offer",
        placeholder="e.g. R99 or Buy 2 Get 1 Free",
    )

    social_link = st.text_input(
        "Social Media / Website Link",
        placeholder="Optional",
    )

    uploaded_images = st.file_uploader(
      "Poster / Images (Optional)",
      type=["png", "jpg", "jpeg", "webp"],
      accept_multiple_files=True,
      help="Upload up to 5 images for your event or promotion.",
    )
    st.divider()

    # ========================================================
    # TERMS
    # ========================================================

    terms = st.checkbox(
        "I agree to the terms and conditions and confirm "
        "that I have permission to submit this event/promotion. "
        "I consent to my information being processed in "
        "accordance with POPIA. *"
    )

    # ========================================================
    # SUBMIT DETAILS
    # ========================================================

    details_submitted = st.form_submit_button(
        "Continue",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# DATE / TIME SECTION
# ============================================================

st.divider()

st.subheader("📅 Date & Time")


# ============================================================
# START DATE
# ============================================================

start_date = st.date_input(
    "Start Date *",
    value=date.today(),
    min_value=date.today(),
    key="start_date",
)


# ============================================================
# OPTIONAL END DATE
# ============================================================

has_end_date = st.checkbox(
    "This promotion has an end date",
    key="has_end_date",
)

end_date = None

if has_end_date:

    end_date = st.date_input(
        "End Date *",
        value=start_date,
        min_value=start_date,
        key="end_date",
    )


# ============================================================
# OPTIONAL START TIME
# ============================================================

has_start_time = st.checkbox(
    "This event/promotion has a specific start time",
    key="has_start_time",
)

start_time = None

if has_start_time:

    start_time = st.time_input(
        "Start Time",
        key="start_time",
    )


# ============================================================
# SUBMISSION
# ============================================================

if details_submitted:

    errors = []

    # ========================================================
    # REQUIRED VALIDATION
    # ========================================================

    if not clean(organizer_name):

        errors.append(
            "Business / Organizer Name is required."
        )

    if not clean(contact):

        errors.append(
            "Contact phone number is required."
        )

    if not clean(event_name):

        errors.append(
            "Event / Promotion Name is required."
        )

    if not clean(description):

        errors.append(
            "Description is required."
        )

    # ========================================================
    # AREA VALIDATION
    # ========================================================

    if not final_areas:

        errors.append(
            "Please select at least one area."
        )

    if (
        "Other" in selected_areas
        and not other_area.strip()
    ):

        errors.append(
            "Please enter your area when selecting Other."
        )

    # ========================================================
    # TERMS VALIDATION
    # ========================================================

    if not terms:

        errors.append(
            "You must agree to the terms and POPIA consent."
        )

    # ========================================================
    # END DATE VALIDATION
    # ========================================================

    if has_end_date:

        if end_date is None:

            errors.append(
                "Please select an End Date."
            )

        elif end_date < start_date:

            errors.append(
                "End Date cannot be before Start Date."
            )

    # ========================================================
    # DISPLAY ERRORS
    # ========================================================

    if errors:

        for error in errors:

            st.error(
                error
            )

    else:

        # ====================================================
        # FORMAT DATES
        # ====================================================

        event_date_value = start_date.strftime(
            "%Y-%m-%d"
        )

        if has_end_date and end_date is not None:

            end_date_value = end_date.strftime(
                "%Y-%m-%d"
            )

        else:

            end_date_value = ""

        # ====================================================
        # FORMAT TIME
        # ====================================================

        if has_start_time and start_time is not None:

            event_time_value = start_time.strftime(
                "%H:%M"
            )

        else:

            event_time_value = ""

        # ====================================================
        # FORMAT MULTIPLE AREAS
        # ====================================================
        #
        # IMPORTANT:
        #
        # Do NOT use:
        #
        #     clean(final_areas)
        #
        # and do NOT use comma separation.
        #
        # Each area can already contain a comma:
        #
        #     Zakheni, KwaMhlanga
        #
        # Therefore we use "|" as the multi-area separator.
        #
        # Example:
        #
        # Zakheni, KwaMhlanga|Leratong, KwaMhlanga
        # ========================================================

        areas_value = "|".join(
          clean(area)
          for area in final_areas
          if clean(area)
        )

        # ====================================================
        # GENERATE EVENT ID
        # ====================================================

        event_id = generate_event_id()

        # ====================================================
        # CREATE RECORD
        # ====================================================

        record = {

            "event_id":
                event_id,

            "event_name":
                clean(event_name),

            "description":
                clean(description),

            "event_date":
                event_date_value,

            "event_time":
                event_time_value,

            "venue":
                clean(venue),

            "area":
                areas_value,

            "category":
                clean(category),

            "ticket_price":
                clean(ticket_price),

            "contact":
                clean(contact),

            "social_link":
                clean(social_link),

            "poster_images":
              " | ".join(
                image.name
                for image in uploaded_images
              )
              if uploaded_images
              else "",

            "status":
                "Active",

            "notification_status":
                "Pending",

            "created_at":
                datetime.now().isoformat(),

            "end_date":
                end_date_value,
        }

        # ====================================================
        # SAVE TO GOOGLE SHEETS
        # ====================================================

        try:

            append_record(
                EVENTS_SHEET,
                record,
            )

            st.success(
                "✅ Your event/promotion has been "
                "submitted successfully!"
            )

            st.info(
                f"Submission ID: {event_id}"
            )

            st.write(
                "Your submission is now available to "
                "the Local Events Admin Dashboard."
            )

            st.info(
                f"""
**Target areas**

{", ".join(final_areas)}

**Category**

{category}
"""
            )

            st.write(
                "Subscribers will only be matched when "
                "their selected area and category match "
                "this event."
            )

        except Exception as exc:

            st.error(
                "Unable to save your submission to Google Sheets."
            )

            st.exception(exc)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align: center;
        color: #777;
        font-size: 14px;
        padding: 15px 0 5px 0;
    ">
        © 2026 LAC Automation Solutions
    </div>
    """,
    unsafe_allow_html=True,
)