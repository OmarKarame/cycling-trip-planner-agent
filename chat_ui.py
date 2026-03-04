import streamlit.components.v1 as components

import folium
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Cycling Trip Planner",
    page_icon="🚴",
    layout="wide",
)

st.title("🚴 Cycling Trip Planner")
st.caption("Plan your next multi-day cycling adventure")

# ─── Session state ────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {}


_ACCUMULATING_KEYS = {
    "find_accommodation", "get_weather", "get_points_of_interest",
}


def merge_trip_data(new_data: dict | None) -> None:
    """Merge new tool results into accumulated trip data."""
    if not new_data:
        return
    for key, value in new_data.items():
        if key in _ACCUMULATING_KEYS:
            existing = st.session_state.trip_data.get(key, [])
            if isinstance(value, list):
                existing.extend(value)
            else:
                existing.append(value)
            st.session_state.trip_data[key] = existing
        else:
            st.session_state.trip_data[key] = value


def format_trip_data_markdown(trip: dict) -> str:
    """Build a compact trip summary from structured tool data.

    Claude's text response already contains the day-by-day narrative, so this
    only adds an aggregated summary with the hard numbers.
    """
    route = trip.get("get_route")
    if not route:
        return ""

    elevation = trip.get("get_elevation_profile")
    accommodations = trip.get("find_accommodation", [])
    budget = trip.get("estimate_budget")

    lines = ["## Trip Summary"]
    lines.append(f"- **Route:** {route['start']} → {route['end']}")
    lines.append(f"- **Total distance:** {route['total_distance_km']:.0f} km")
    lines.append(f"- **Duration:** {route['estimated_days']} days")

    if elevation:
        lines.append(f"- **Elevation gain:** {elevation['total_elevation_gain_m']:.0f} m")
        lines.append(f"- **Max elevation:** {elevation['max_elevation_m']:.0f} m")
        lines.append(f"- **Difficulty:** {elevation['difficulty'].capitalize()}")

    if accommodations:
        total_min = 0.0
        total_max = 0.0
        for a in accommodations:
            prices = [acc["price_per_night"] for acc in a.get("accommodations", [])]
            if prices:
                total_min += min(prices)
                total_max += max(prices)
        lines.append(
            f"- **Accommodation estimate:** €{total_min:.0f}–€{total_max:.0f} total"
        )

    if budget:
        if isinstance(budget, list):
            budget = budget[-1]
        total = budget["total_estimate"]
        lines.append(
            f"- **Total budget estimate:** €{total['total']:.0f} "
            f"({budget['currency']})"
        )

    return "\n".join(lines)


# ─── Layout: chat left, map right ────────────────────────────

col_chat, col_map = st.columns([1, 1])

# ─── Chat column ─────────────────────────────────────────────

with col_chat:
    chat_container = st.container(height=700)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Describe your cycling trip..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Planning..."):
                    payload = {"message": prompt}
                    if st.session_state.session_id:
                        payload["session_id"] = st.session_state.session_id

                    try:
                        resp = requests.post(
                            f"{API_URL}/chat", json=payload, timeout=120
                        )
                        resp.raise_for_status()
                        data = resp.json()

                        st.session_state.session_id = data["session_id"]
                        assistant_msg = data["response"]
                        merge_trip_data(data.get("trip_data"))

                        # Append structured data summary to the chat message
                        data_md = format_trip_data_markdown(st.session_state.trip_data)
                        if data_md and data.get("tools_used"):
                            assistant_msg += "\n\n---\n\n" + data_md

                    except requests.exceptions.ConnectionError:
                        assistant_msg = (
                            "Could not connect to the API. "
                            "Make sure the server is running: `uvicorn main:app --reload`"
                        )
                    except Exception as e:
                        assistant_msg = f"Error: {e}"

                st.markdown(assistant_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_msg}
                )
        st.rerun()

# ─── Map column ───────────────────────────────────────────────

with col_map:
    trip = st.session_state.trip_data
    route = trip.get("get_route")

    if route:
        waypoints = route.get("waypoints", [])
        weather_list = trip.get("get_weather", [])
        accommodations = trip.get("find_accommodation", [])

        # Build lookups for popup details
        weather_by_loc = {w["location"].lower(): w for w in weather_list}
        acc_by_loc = {a["location"].lower(): a for a in accommodations}

        coords = [(wp["latitude"], wp["longitude"]) for wp in waypoints]

        mid_idx = len(coords) // 2
        m = folium.Map(location=coords[mid_idx], zoom_start=6)

        folium.PolyLine(
            locations=coords, weight=4, color="#2563eb", opacity=0.8
        ).add_to(m)

        for i, wp in enumerate(waypoints):
            is_start = i == 0
            is_end = i == len(waypoints) - 1

            if is_start:
                color = "green"
            elif is_end:
                color = "red"
            else:
                color = "blue"

            # Build rich popup HTML
            popup_lines = [
                f"<div style='min-width:220px;font-family:sans-serif;font-size:13px'>",
                f"<h4 style='margin:0 0 6px'>{'🟢' if is_start else '🔴' if is_end else '🔵'} {wp['name']}</h4>",
                f"<b>Day {wp['day']}</b>",
            ]

            wp_weather = weather_by_loc.get(wp["name"].lower())
            if wp_weather:
                popup_lines.append("<hr style='margin:6px 0'>")
                popup_lines.append(
                    f"🌤 <b>{wp_weather['avg_temp_celsius']:.0f}°C</b> · "
                    f"{wp_weather['rain_chance_percent']:.0f}% rain · "
                    f"{wp_weather['wind_speed_kmh']:.0f} km/h wind"
                )
                popup_lines.append(f"<br><i>{wp_weather['summary']}</i>")

            wp_acc = acc_by_loc.get(wp["name"].lower())
            if wp_acc:
                popup_lines.append("<hr style='margin:6px 0'>")
                popup_lines.append("🏨 <b>Accommodation:</b><br>")
                for acc in wp_acc.get("accommodations", [])[:3]:
                    popup_lines.append(
                        f"&nbsp;&nbsp;• {acc['name']} ({acc['type']}) — "
                        f"€{acc['price_per_night']:.0f}/night<br>"
                    )

            popup_lines.append("</div>")
            popup_html = "\n".join(popup_lines)

            folium.CircleMarker(
                location=(wp["latitude"], wp["longitude"]),
                radius=8 if (is_start or is_end) else 5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=wp["name"],
            ).add_to(m)

        m.fit_bounds(coords)

        st.subheader("Route Map")
        map_html = m._repr_html_()
        components.html(map_html, height=500)

        r_col1, r_col2 = st.columns(2)
        r_col1.metric("Total Distance", f"{route['total_distance_km']:.0f} km")
        r_col2.metric("Estimated Days", route["estimated_days"])

        # ─── Expandable day-by-day details below map ─────────────
        days: dict[int, list[dict]] = {}
        for wp in waypoints:
            days.setdefault(wp["day"], []).append(wp)

        for day_num in sorted(days.keys()):
            day_wps = days[day_num]
            from_name = day_wps[0]["name"]
            to_name = day_wps[-1]["name"] if len(day_wps) > 1 else from_name
            label = f"Day {day_num}: {from_name} → {to_name}"

            with st.expander(label):
                # Weather
                day_weather = None
                for wp in day_wps:
                    if wp["name"].lower() in weather_by_loc:
                        day_weather = weather_by_loc[wp["name"].lower()]
                        break
                if day_weather:
                    st.markdown(
                        f"**Weather:** {day_weather['avg_temp_celsius']:.0f}°C, "
                        f"{day_weather['rain_chance_percent']:.0f}% rain, "
                        f"{day_weather['wind_speed_kmh']:.0f} km/h wind  \n"
                        f"*{day_weather['summary']}*"
                    )

                # Accommodation
                day_acc = None
                for wp in day_wps:
                    if wp["name"].lower() in acc_by_loc:
                        day_acc = acc_by_loc[wp["name"].lower()]
                        break
                if day_acc:
                    st.markdown("**Accommodation options:**")
                    for acc in day_acc.get("accommodations", []):
                        st.markdown(
                            f"- {acc['name']} ({acc['type']}) — "
                            f"€{acc['price_per_night']:.0f}/night, "
                            f"★ {acc['rating']:.1f}"
                        )

                # Waypoints for this day
                wp_names = [wp["name"] for wp in day_wps]
                st.markdown(f"**Stops:** {' → '.join(wp_names)}")

    else:
        st.info("The route map will appear here once you start planning a trip.")
