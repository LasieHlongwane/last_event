# google_places.py

import os
import requests
import streamlit as st


AUTOCOMPLETE_URL = (
    "https://places.googleapis.com/v1/places:autocomplete"
)

PLACE_DETAILS_URL = (
    "https://places.googleapis.com/v1/places/{place_id}"
)


def get_google_api_key():
    """
    Get Google Maps/Places API key.

    Recommended:
    Store it as an environment variable:

        GOOGLE_MAPS_API_KEY

    """

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get(
                "GOOGLE_MAPS_API_KEY"
            )
        except Exception:
            api_key = None

    if not api_key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY is not configured."
        )

    return api_key


def search_south_africa_places(
    search_text,
):
    """
    Search for geographical locations in South Africa.

    Results are restricted to South Africa.

    Returns:

        [
            {
                "description": "...",
                "place_id": "..."
            }
        ]
    """

    search_text = str(
        search_text or ""
    ).strip()

    if len(search_text) < 2:
        return []

    api_key = get_google_api_key()

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "suggestions.placePrediction.placeId,"
            "suggestions.placePrediction.text,"
            "suggestions.placePrediction.structuredFormat"
        ),
    }

    payload = {
        "input": search_text,

        # SOUTH AFRICA ONLY
        "includedRegionCodes": [
            "za"
        ],

        # We are looking for geographical areas,
        # not businesses.
        "includedPrimaryTypes": [
            "(regions)"
        ],

        "languageCode": "en",

        # Do not return search/query predictions.
        "includeQueryPredictions": False,
    }

    session = requests.Session()

# Prevent Streamlit/Windows environment proxy settings
# from interfering with the Google HTTPS connection.
    session.trust_env = False

    headers["Connection"] = "close"

    response = session.post(
      AUTOCOMPLETE_URL,
      json=payload,
      headers=headers,
      timeout=(10, 30),
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for suggestion in data.get(
        "suggestions",
        [],
    ):

        prediction = suggestion.get(
            "placePrediction"
        )

        if not prediction:
            continue

        place_id = prediction.get(
            "placeId"
        )

        text_data = prediction.get(
            "text",
            {}
        )

        description = text_data.get(
            "text",
            ""
        )

        if not place_id or not description:
            continue

        results.append(
            {
                "description":
                    description,

                "place_id":
                    place_id,
            }
        )

    return results


def get_place_details(
    place_id,
):
    """
    Get the selected location's:

    - name
    - formatted address
    - latitude
    - longitude
    - place ID
    """

    if not place_id:
        return None

    api_key = get_google_api_key()

    url = PLACE_DETAILS_URL.format(
        place_id=place_id
    )

    headers = {
        "X-Goog-Api-Key": api_key,

        "X-Goog-FieldMask": (
            "id,"
            "displayName,"
            "formattedAddress,"
            "location"
        ),
    }

    session = requests.Session()
    session.trust_env = False

    headers["Connection"] = "close"

    response = session.get(
      url,
      headers=headers,
      timeout=(10, 30),
    )

    response.raise_for_status()

    response.raise_for_status()

    data = response.json()

    location = data.get(
        "location",
        {}
    )

    display_name = data.get(
        "displayName",
        {}
    )

    return {
        "place_id":
            data.get(
                "id",
                place_id,
            ),

        "name":
            display_name.get(
                "text",
                "",
            ),

        "formatted_address":
            data.get(
                "formattedAddress",
                "",
            ),

        "latitude":
            location.get(
                "latitude"
            ),

        "longitude":
            location.get(
                "longitude"
            ),
    }


def location_autocomplete(
    label="Area",
    key_prefix="location",
):
    """
    Reusable Streamlit South African
    location selector.

    Returns:

        {
            "name": "...",
            "formatted_address": "...",
            "place_id": "...",
            "latitude": ...,
            "longitude": ...
        }

    or None if no location has been selected.
    """

    search_key = (
        f"{key_prefix}_search"
    )

    selected_key = (
        f"{key_prefix}_selected"
    )

    details_key = (
        f"{key_prefix}_details"
    )

    search_text = st.text_input(
        label,
        placeholder=(
            "Start typing a South African area..."
        ),
        key=search_key,
    )

    if not search_text:
        return None

    if len(search_text.strip()) < 2:

        st.caption(
            "Type at least 2 characters."
        )

        return None

    try:

        suggestions = (
            search_south_africa_places(
                search_text
            )
        )

    except Exception as exc:

        st.error(
            "Unable to search Google Places."
        )

        st.exception(exc)

        return None

    if not suggestions:

        st.info(
            "No South African locations found."
        )

        return None

    option_labels = [
        item["description"]
        for item in suggestions
    ]

    selected_label = st.selectbox(
        "Select location",
        option_labels,
        key=selected_key,
    )

    selected_place = next(
        (
            item
            for item in suggestions
            if item["description"]
            == selected_label
        ),
        None,
    )

    if not selected_place:
        return None

    place_id = selected_place[
        "place_id"
    ]

    # Avoid repeatedly requesting Place Details
    # for the same selected place.
    cached_details = st.session_state.get(
        details_key
    )

    if (
        cached_details
        and cached_details.get(
            "place_id"
        )
        == place_id
    ):
        return cached_details

    try:

        details = get_place_details(
            place_id
        )

    except Exception as exc:

        st.error(
            "Unable to load selected location details."
        )

        st.exception(exc)

        return None

    st.session_state[
        details_key
    ] = details

    st.success(
        f"Selected: {details.get('formatted_address', details.get('name', ''))}"
    )

    return details