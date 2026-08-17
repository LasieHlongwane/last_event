import streamlit as st
from datetime import datetime
import uuid

from sheets import get_all_records, append_record


# ============================================================
# CONFIGURATION
# ============================================================

USERS_SHEET = "Users"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Local Alerts",
    page_icon="📱",
    layout="centered",
)


# ============================================================
# HELPERS
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize_phone(phone):
    """
    Convert common South African phone formats to:

        27761234567
    """

    phone = normalize(phone)

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

    elif len(phone) == 9:
        phone = "27" + phone

    return phone


def is_yes(value):
    return normalize(value).lower() in [
        "yes",
        "true",
        "1",
        "y",
    ]


def generate_user_id():
    return (
        "USR-"
        + uuid.uuid4().hex[:8].upper()
    )


def phone_exists(phone):

    users = get_all_records(
        USERS_SHEET
    )

    phone = normalize_phone(phone)

    for user in users:

        existing_phone = normalize_phone(
            user.get("phone")
        )

        if existing_phone == phone:
            return True

    return False


# ============================================================
# AREA OPTIONS
# ============================================================

AREA_OPTIONS = [
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
# HEADER
# ============================================================

st.title("📱 LAC Local Alerts")

st.write(
    """
Get local events, deals and promotions sent directly
to your phone.
"""
)

# ============================================================
# LOCATION
# ============================================================

st.subheader("📍 Location")

selected_areas = st.multiselect(
    "Area *",
    AREA_OPTIONS,
    placeholder="Select one or more areas...",
    key="user_areas",
)


# ============================================================
# OTHER AREA
# ============================================================

other_area = ""

if "Other" in selected_areas:

    other_area = st.text_input(
        "Enter your area *",
        placeholder="e.g. Mmametlhake, KwaMhlanga",
        key="user_other_area",
        help=(
            "Enter the name of your village, section, "
            "complex or area."
        ),
    )


# ============================================================
# FINAL AREA LIST
# ============================================================

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


# ============================================================
# REGISTRATION FORM
# ============================================================

with st.form("user_registration_form"):

    st.subheader("Details")

    name = st.text_input(
        "Name",
        placeholder="Enter your name",
    )

    phone = st.text_input(
        "Phone Number",
        placeholder="e.g. 0761234567",
        help="Enter your South African mobile number.",
    )

    st.subheader(
        "I Wanna Stay Informed About..."
    )

    categories = st.multiselect(
        "Select your interests",
        CATEGORY_OPTIONS,
    )

    st.subheader(
        "Notification Method"
    )

    notification_channel = st.selectbox(
        "How should we notify you?",
        [
            "WhatsApp",
            "SMS",
            "Both",
        ],
    )

    # ========================================================
    # CHANNEL OPT-IN
    # ========================================================

    whatsapp_opt_in = False
    sms_opt_in = False

    if notification_channel in [
        "WhatsApp",
        "Both",
    ]:

        whatsapp_opt_in = st.checkbox(
            "I agree to receive WhatsApp notifications."
        )

    if notification_channel in [
        "SMS",
        "Both",
    ]:

        sms_opt_in = st.checkbox(
            "I agree to receive SMS notifications."
        )

    # ========================================================
    # TERMS
    # ========================================================

    st.subheader(
        "Terms & Privacy"
    )

    st.caption(
        """
By registering, you agree that your information may be
used to provide you with local event, deal and promotional
notifications according to our Terms & Conditions and
Privacy Policy.
"""
    )

    terms_accepted = st.checkbox(
        "I agree to the Terms & Conditions and POPIA consent."
    )

    submitted = st.form_submit_button(
        "📱 JOIN LOCAL ALERTS",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# PROCESS SUBMISSION
# ============================================================

if submitted:

    errors = []

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not normalize(name):

        errors.append(
            "Please enter your name."
        )

    if not normalize(phone):

        errors.append(
            "Please enter your phone number."
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
    # PHONE VALIDATION
    # ========================================================

    normalized_phone = normalize_phone(
        phone
    )

    if normalized_phone:

        if not (
            normalized_phone.startswith("27")
            and len(normalized_phone) == 11
        ):

            errors.append(
                "Please enter a valid South African mobile number."
            )

    # ========================================================
    # CATEGORY VALIDATION
    # ========================================================

    if not categories:

        errors.append(
            "Please select at least one category."
        )

    # ========================================================
    # CHANNEL VALIDATION
    # ========================================================

    if notification_channel == "WhatsApp":

        if not whatsapp_opt_in:

            errors.append(
                "Please agree to receive WhatsApp notifications."
            )

    elif notification_channel == "SMS":

        if not sms_opt_in:

            errors.append(
                "Please agree to receive SMS notifications."
            )

    elif notification_channel == "Both":

        if not whatsapp_opt_in:

            errors.append(
                "Please agree to receive WhatsApp notifications."
            )

        if not sms_opt_in:

            errors.append(
                "Please agree to receive SMS notifications."
            )

    # ========================================================
    # TERMS
    # ========================================================

    if not terms_accepted:

        errors.append(
            "You must accept the Terms & Conditions and POPIA consent."
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
        # DUPLICATE PHONE CHECK
        # ====================================================

        try:

            if phone_exists(
                normalized_phone
            ):

                st.warning(
                    """
This phone number is already registered.

If you want to change your notification
preferences, please contact the administrator.
"""
                )

                st.stop()

        except Exception as exc:

            st.error(
                "Unable to check registration: "
                f"{exc}"
            )

            st.stop()

        # ====================================================
        # SAVE MULTIPLE AREAS USING PIPE |
        # ====================================================
        #
        # IMPORTANT:
        #
        # We DO NOT use:
        #
        #     ", ".join(final_areas)
        #
        # because an area itself contains a comma:
        #
        #     Zakheni, KwaMhlanga
        #
        # Therefore the Google Sheet will contain:
        #
        # Zakheni, KwaMhlanga|Leratong, KwaMhlanga
        #
        # The matching engine can safely split on "|".
        # ====================================================

        areas_value = "|".join(
            final_areas
        )

        categories_value = ", ".join(
            categories
        )

        # ====================================================
        # CREATE USER
        # ====================================================

        user_record = {

            "user_id":
                generate_user_id(),

            "name":
                normalize(name),

            "phone":
                normalized_phone,

            "areas":
                areas_value,

            "categories":
                categories_value,

            "notification_channel":
                notification_channel,

            "active":
                "Yes",

            "whatsapp_opt_in":
                "Yes"
                if whatsapp_opt_in
                else "No",

            "sms_opt_in":
                "Yes"
                if sms_opt_in
                else "No",

            "created_at":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
        }

        # ====================================================
        # SAVE TO GOOGLE SHEETS
        # ====================================================

        try:

            append_record(
                USERS_SHEET,
                user_record,
            )

            st.success(
                "🎉 Registration successful!"
            )

            st.write(
                f"Welcome, **{name}**!"
            )

            st.write(
                "You will now receive local notifications "
                "based on your selected areas and interests."
            )

            st.info(
                f"""
**Your preferences**

Areas: {", ".join(final_areas)}

Categories: {", ".join(categories)}

Notification: {notification_channel}
"""
            )

        except Exception as exc:

            st.error(
                "Your registration could not be saved. "
                f"Please try again later.\n\n{exc}"
            )


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