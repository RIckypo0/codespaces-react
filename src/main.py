"""Medication Reminder — Streamlit app with Supabase email/password accounts.

Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit's private Secrets settings.
Run locally with: streamlit run main.py
"""

from datetime import date, datetime
from io import BytesIO
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from PIL import Image
import pytesseract
from supabase import create_client


st.set_page_config(page_title="Medication Reminder", page_icon="💊", layout="centered")


def configured_supabase_client():
    """Return a client for this browser session, or None when not configured."""
    if st.session_state.get("supabase_client"):
        return st.session_state.supabase_client

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except (KeyError, StreamlitSecretNotFoundError):
        return None

    client = create_client(url, key)
    st.session_state.supabase_client = client
    return client


def signed_in_user_id():
    return st.session_state.get("user_id")


def set_signed_in_user(user):
    st.session_state.user_id = user.id
    st.session_state.user_email = user.email or ""


def time_choices():
    """Create five-minute time choices with AM/PM labels."""
    result = []
    for hour in range(24):
        for minute in range(0, 60, 5):
            value = f"{hour:02d}:{minute:02d}"
            label = datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")
            result.append((label, value))
    return result


def show_setup_instructions():
    st.title("Medication Reminder")
    st.info("Connect a Supabase project to enable accounts and private schedules.")
    st.markdown(
        """
        **Setup checklist**

        1. Create a Supabase project.
        2. In its SQL Editor, run the SQL in `supabase_setup.sql`.
        3. In Streamlit Cloud, open your app's **Settings → Secrets** and add:

        ```toml
        SUPABASE_URL = "your-project-url"
        SUPABASE_ANON_KEY = "your-publishable-or-anon-key"
        ```

        Use the publishable/anon key only. **Never put a service-role key in this
        app or in GitHub.** The SQL enables row-level security so each account
        can access only its own records.
        """
    )
    st.caption(
        "For local testing, put those settings in `.streamlit/secrets.toml` "
        "and do not commit that file."
    )


def render_auth(client):
    st.title("💊 Medication Reminder")
    st.caption("Create an account to keep a private medication schedule.")
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            try:
                result = client.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
                if result.user:
                    set_signed_in_user(result.user)
                    st.rerun()
                st.error("Sign-in did not return a user. Please try again.")
            except Exception:
                st.error("Could not sign in. Check your email and password.")

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email address")
            password = st.text_input("Password (at least 8 characters)", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary")
        if submitted:
            if "@" not in email or not email.strip():
                st.error("Enter a valid email address.")
            elif len(password) < 8:
                st.error("Choose a password with at least 8 characters.")
            elif password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    result = client.auth.sign_up(
                        {"email": email.strip(), "password": password}
                    )
                    if result.session and result.user:
                        set_signed_in_user(result.user)
                        st.success("Account created.")
                        st.rerun()
                    else:
                        st.success(
                            "Account created. Check your email to confirm it, "
                            "then sign in."
                        )
                except Exception:
                    st.error(
                        "Could not create the account. Check the email address "
                        "or try signing in if you already registered."
                    )


def load_medications(client, user_id):
    return (
        client.table("medications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
        .data
    )


def load_history(client, user_id):
    return (
        client.table("dose_logs")
        .select("*")
        .eq("user_id", user_id)
        .order("completed_at", desc=True)
        .execute()
        .data
    )


def render_app(client, user_id):
    times = time_choices()
    label_to_value = {label: value for label, value in times}
    value_to_label = {value: label for label, value in times}

    st.title("💊 Medication Reminder")
    st.caption(f"Signed in as {st.session_state.get('user_email', '')}")
    if st.button("Sign out"):
        try:
            client.auth.sign_out()
        finally:
            st.session_state.pop("user_id", None)
            st.session_state.pop("user_email", None)
            st.session_state.pop("supabase_client", None)
            st.rerun()

    st.warning(
        "This app is a tracking aid, not a substitute for instructions from "
        "your healthcare professional. It does not send phone alarms."
    )

    try:
        medications = load_medications(client, user_id)
        history = load_history(client, user_id)
    except Exception:
        st.error(
            "Could not load your schedule. Check that you ran `supabase_setup.sql` "
            "and enabled its row-level security policies."
        )
        return

    today_tab, medicines_tab, history_tab = st.tabs(
        ["Today's schedule", "My medicines", "Taken history"]
    )

    with medicines_tab:
        st.subheader("Add a medicine")
        st.caption(
            "Optional: take a clear photo of the label and copy the recognized "
            "text into your notes. Always check it against the package."
        )
        label_photo = st.camera_input("Photograph the medicine label")
        if label_photo is not None and st.button(
            "Read label text", key="read_label_text"
        ):
            try:
                image = Image.open(BytesIO(label_photo.getvalue())).convert("RGB")
                recognized_text = pytesseract.image_to_string(image).strip()
                if recognized_text:
                    st.session_state["new_notes"] = recognized_text
                    st.success(
                        "Text recognized. Review and correct it in Instructions or notes below."
                    )
                    st.rerun()
                else:
                    st.warning(
                        "No text was recognized. Try a brighter, closer photo with the label in focus."
                    )
            except Exception:
                st.error(
                    "The label reader is unavailable. You can still type the instructions manually."
                )

        if st.session_state.get("new_notes"):
            st.info(
                "The recognized label text is only a draft. Verify every detail "
                "before relying on it."
            )
        with st.form("add_medication_form", clear_on_submit=True):
            name = st.text_input("Medicine name")
            dose = st.text_input("Dose")
            selected_times = st.multiselect(
                "Reminder times",
                [label for label, _ in times],
                help="Choose one or more times. Times are shown in AM/PM.",
            )
            notes = st.text_area(
                "Instructions or notes",
                value=st.session_state.get("new_notes", ""),
                key="new_notes",
            )
            submitted = st.form_submit_button("Add medicine")

        if submitted:
            if not name.strip():
                st.error("Enter a medicine name.")
            elif not selected_times:
                st.error("Choose at least one reminder time.")
            else:
                try:
                    client.table("medications").insert(
                        {
                            "user_id": user_id,
                            "name": name.strip(),
                            "dose": dose.strip(),
                            "times": sorted(
                                label_to_value[label] for label in selected_times
                            ),
                            "notes": notes.strip(),
                        }
                    ).execute()
                    st.session_state.pop("new_notes", None)
                    st.rerun()
                except Exception:
                    st.error("Could not save that medicine. Please try again.")

        st.divider()
        st.subheader("Saved medicines")
        if not medications:
            st.info("No medicines saved yet.")

        for medication in medications:
            med_id = medication["id"]
            with st.expander(medication["name"]):
                with st.form(f"edit_{med_id}"):
                    updated_name = st.text_input(
                        "Medicine name", medication["name"], key=f"name_{med_id}"
                    )
                    updated_dose = st.text_input(
                        "Dose", medication.get("dose", ""), key=f"dose_{med_id}"
                    )
                    current_labels = [
                        value_to_label[value]
                        for value in medication.get("times", [])
                        if value in value_to_label
                    ]
                    updated_times = st.multiselect(
                        "Reminder times",
                        [label for label, _ in times],
                        default=current_labels,
                        key=f"times_{med_id}",
                    )
                    updated_notes = st.text_area(
                        "Instructions or notes",
                        medication.get("notes", ""),
                        key=f"notes_{med_id}",
                    )
                    save_clicked = st.form_submit_button("Save changes")

                if save_clicked:
                    if not updated_name.strip() or not updated_times:
                        st.error("Enter a name and choose at least one time.")
                    else:
                        try:
                            client.table("medications").update(
                                {
                                    "name": updated_name.strip(),
                                    "dose": updated_dose.strip(),
                                    "times": sorted(
                                        label_to_value[label] for label in updated_times
                                    ),
                                    "notes": updated_notes.strip(),
                                }
                            ).eq("id", med_id).eq("user_id", user_id).execute()
                            st.rerun()
                        except Exception:
                            st.error("Could not save those changes.")

                if st.button("Delete medicine", key=f"delete_{med_id}"):
                    try:
                        client.table("medications").delete().eq(
                            "id", med_id
                        ).eq("user_id", user_id).execute()
                        st.rerun()
                    except Exception:
                        st.error("Could not delete that medicine.")

    with today_tab:
        st.subheader(date.today().strftime("%A, %B %d").replace(" 0", " "))
        today_key = date.today().isoformat()
        scheduled = sorted(
            [
                (time_value, medication)
                for medication in medications
                for time_value in medication.get("times", [])
            ],
            key=lambda item: item[0],
        )
        if not scheduled:
            st.info("Your schedule is empty. Add a medicine in My medicines.")

        for time_value, medication in scheduled:
            dose_key = f"{today_key}|{medication['id']}|{time_value}"
            already_taken = any(
                row["dose_key"] == dose_key for row in history
            )
            with st.container(border=True):
                label = value_to_label.get(time_value, time_value)
                st.markdown(f"### {label} · {medication['name']}")
                st.write(f"**Dose:** {medication.get('dose') or 'Not entered'}")
                if medication.get("notes"):
                    st.caption(medication["notes"])
                if already_taken:
                    st.success("Marked as taken.")
                elif st.button("Mark as taken", key=f"taken_{dose_key}"):
                    try:
                        client.table("dose_logs").insert(
                            {
                                "user_id": user_id,
                                "dose_key": dose_key,
                                "medication_id": medication["id"],
                                "medication_name": medication["name"],
                                "dose": medication.get("dose", ""),
                                "scheduled_time": time_value,
                                "taken_date": today_key,
                            }
                        ).execute()
                        st.rerun()
                    except Exception:
                        st.error("Could not record this check-in.")

    with history_tab:
        st.subheader("Doses marked as taken")
        if not history:
            st.info("Your check-ins will appear here.")
        for row in history:
            completed = row.get("completed_at", "")
            time_text = value_to_label.get(
                row.get("scheduled_time", ""), row.get("scheduled_time", "")
            )
            st.write(
                f"**{row['medication_name']}** · {time_text} on "
                f"{row['taken_date']} · Dose: {row.get('dose') or 'Not entered'}"
            )
            if completed:
                st.caption(f"Recorded: {completed}")
            st.divider()


client = configured_supabase_client()
if client is None:
    show_setup_instructions()
elif signed_in_user_id():
    render_app(client, signed_in_user_id())
else:
    render_auth(client)
