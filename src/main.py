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


st.set_page_config(page_title="Medication Reminder", page_icon="💊", layout="wide")


def apply_app_theme():
    """Give the browser app a calm, readable visual style."""
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: #f5f8f5;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 980px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stHeader"] {
            background: rgba(245, 248, 245, 0.85);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #dce8df;
            border-radius: 16px;
            background: #ffffff;
        }
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"] {
            background: #176b54;
            border-color: #176b54;
            color: #ffffff;
            border-radius: 10px;
            font-weight: 650;
        }
        div.stButton > button[kind="primary"]:hover,
        div.stFormSubmitButton > button[kind="primary"]:hover {
            background: #105440;
            border-color: #105440;
            color: #ffffff;
        }
        .med-brand {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 0 0 1rem;
            padding: 1.35rem 1.5rem;
            border: 1px solid #dce8df;
            border-radius: 20px;
            background: linear-gradient(120deg, #ffffff 0%, #e9f4ed 100%);
        }
        .med-brand-icon {
            display: grid;
            place-items: center;
            width: 54px;
            height: 54px;
            flex: 0 0 54px;
            border-radius: 16px;
            background: #d8eee0;
            font-size: 28px;
        }
        .med-brand-kicker {
            margin: 0 0 3px;
            color: #176b54;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .med-brand h1 {
            margin: 0;
            color: #173c31;
            font-size: clamp(1.65rem, 4vw, 2.25rem);
            line-height: 1.15;
        }
        .med-brand-copy {
            margin: 6px 0 0;
            color: #52665b;
            font-size: 0.98rem;
        }
        .progress-label {
            color: #176b54;
            font-weight: 700;
        }
        @media (max-width: 600px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1rem 1rem 2rem;
            }
            .med-brand {
                gap: 12px;
                padding: 1rem;
            }
            .med-brand-icon {
                width: 46px;
                height: 46px;
                flex-basis: 46px;
                font-size: 24px;
            }
        }
        :root {
            color-scheme: light;
            --care-ink: #203b32;
            --care-muted: #5e746a;
            --care-green: #236b52;
            --care-green-deep: #18543f;
            --care-paper: #f6f8f3;
            --care-line: #d9e5dc;
            --care-white: #fffefa;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(ellipse at 7% 2%, rgba(213, 235, 219, .6), transparent 31rem),
                var(--care-paper);
            color: var(--care-ink);
        }
        [data-testid="stAppViewContainer"]::before {
            content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .15;
            background-image: radial-gradient(#769181 .55px, transparent .55px);
            background-size: 17px 17px;
            mask-image: linear-gradient(to bottom, black, transparent 70%);
        }
        [data-testid="stMainBlockContainer"] { max-width: 1040px; padding: 2.3rem 2rem 4rem; }
        [data-testid="stHeader"] { background: rgba(246, 248, 243, .82); }
        h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] { color: var(--care-ink); }
        h2, h3 { letter-spacing: -.025em; }
        [data-testid="stCaptionContainer"], .stCaption { color: var(--care-muted); }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--care-line); border-radius: 19px;
            background: rgba(255, 254, 250, .88); box-shadow: 0 7px 24px rgba(39, 75, 55, .045);
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: .45rem; border-bottom: 1px solid var(--care-line);
        }
        [data-testid="stTabs"] button[data-baseweb="tab"] {
            min-height: 3rem; padding: .65rem 1.05rem; border-radius: 12px 12px 0 0;
            color: var(--care-muted); font-weight: 650;
        }
        [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--care-green-deep); background: #e8f2eb;
        }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--care-green); }
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            border-color: #cbdacf; border-radius: 11px; background-color: var(--care-white);
        }
        [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
            border-color: var(--care-green); box-shadow: 0 0 0 2px rgba(35, 107, 82, .15);
        }
        [data-testid="stForm"] {
            padding: 1rem 1.15rem 1.15rem; border: 1px solid #e0e9e1;
            border-radius: 16px; background: rgba(255, 254, 250, .72);
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--care-line); border-radius: 14px;
            overflow: hidden; background: rgba(255, 254, 250, .75);
        }
        [data-testid="stAlert"] { border-radius: 14px; border-width: 1px; }
        [data-testid="stProgress"] > div > div { background-color: var(--care-green); }
        [data-testid="stMetric"] {
            padding: .85rem 1rem; border: 1px solid #dce9df;
            border-radius: 14px; background: #f0f6f0;
        }
        [data-testid="stMetricLabel"] { color: var(--care-muted); }
        [data-testid="stMetricValue"] { color: var(--care-green-deep); }
        [data-testid="stCameraInput"] {
            padding: .5rem; border: 1px dashed #b9cdbd;
            border-radius: 14px; background: #f4f8f3;
        }
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
            min-height: 2.75rem; padding: .55rem 1.1rem; background: var(--care-green);
            border-color: var(--care-green); color: #ffffff; border-radius: 11px;
            font-weight: 700; transition: background-color .16s ease, transform .16s ease;
        }
        div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {
            background: var(--care-green-deep); border-color: var(--care-green-deep);
            color: #ffffff; transform: translateY(-1px);
        }
        div.stButton > button:not([kind="primary"]), div.stFormSubmitButton > button:not([kind="primary"]) {
            min-height: 2.65rem; border-radius: 11px; border-color: #cbdacf;
            color: var(--care-green-deep); background: var(--care-white); font-weight: 650;
        }
        button:focus-visible, a:focus-visible, input:focus-visible,
        textarea:focus-visible, [role="combobox"]:focus-visible {
            outline: 3px solid rgba(35, 107, 82, .55) !important; outline-offset: 2px !important;
        }
        .med-brand {
            position: relative; overflow: hidden; padding: 1.45rem 1.65rem;
            border: 1px solid #d6e5d9; border-radius: 22px;
            background: linear-gradient(112deg, #fffefa 0%, #eef6ee 63%, #e4f0e7 100%);
            box-shadow: 0 12px 34px rgba(39, 75, 55, .07);
        }
        .med-brand::after {
            content: ""; position: absolute; width: 190px; height: 190px; right: -52px; top: -107px;
            border: 1px solid rgba(35, 107, 82, .13); border-radius: 50%;
            box-shadow: 0 0 0 22px rgba(35, 107, 82, .035), 0 0 0 45px rgba(35, 107, 82, .025);
            pointer-events: none;
        }
        .med-brand-icon {
            background: #d9ecde; color: var(--care-green-deep); border-radius: 17px;
        }
        .med-brand-icon svg { width: 30px; height: 30px; }
        .med-brand-content { position: relative; z-index: 1; }
        .med-brand-kicker {
            color: var(--care-green); font-size: .72rem; letter-spacing: .13em;
        }
        .med-brand h1 {
            color: #1d4033; font-size: clamp(1.7rem, 4vw, 2.35rem);
            line-height: 1.12; letter-spacing: -.04em;
        }
        .med-brand-copy { margin: 7px 0 0; color: #52695e; font-size: 1rem; }
        .progress-label { color: var(--care-green-deep); font-weight: 700; }
        [data-testid="stForm"] label { font-weight: 600; }
        @media (max-width: 600px) {
            [data-testid="stMainBlockContainer"] { padding: 1rem 1rem 2.5rem; }
            .med-brand { gap: 12px; padding: 1.05rem; border-radius: 18px; }
            .med-brand-icon { width: 46px; height: 46px; flex-basis: 46px; }
            .med-brand-icon svg { width: 26px; height: 26px; }
            .med-brand-copy { font-size: .92rem; }
            [data-testid="stTabs"] button[data-baseweb="tab"] { padding-inline: .7rem; font-size: .91rem; }
            [data-testid="stForm"] { padding: .8rem; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { transition-duration: .01ms !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header(copy):
    st.markdown(
        f"""
        <div class="med-brand">
            <div class="med-brand-icon" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <g transform="rotate(-42 16 16)">
                        <rect x="7" y="5" width="18" height="22" rx="9" fill="#236b52"/>
                        <path d="M7 16h18" stroke="#f8fff8" stroke-width="2"/>
                        <path d="M16 6v10" stroke="#b8dbc1" stroke-width="1.5"/>
                    </g>
                </svg>
            </div>
            <div class="med-brand-content">
                <p class="med-brand-kicker">Your daily care, organized</p>
                <h1>Medication Reminder</h1>
                <p class="med-brand-copy">{copy}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


apply_app_theme()


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
    render_brand_header("A simple, private place to manage your medicine schedule.")
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

    render_brand_header("Your schedule at a glance, with simple daily check-ins.")
    account_col, signout_col = st.columns([5, 1])
    with account_col:
        st.caption(f"Signed in as {st.session_state.get('user_email', '')}")
    with signout_col:
        if st.button("Sign out"):
            try:
                client.auth.sign_out()
            finally:
                st.session_state.pop("user_id", None)
                st.session_state.pop("user_email", None)
                st.session_state.pop("supabase_client", None)
                st.rerun()

    st.caption(
        "A tracking aid only—not medical advice or a substitute for "
        "instructions from your healthcare professional."
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
        taken_keys = {row.get("dose_key") for row in history}
        taken_count = sum(
            1
            for time_value, medication in scheduled
            if f"{today_key}|{medication['id']}|{time_value}" in taken_keys
        )
        total_count = len(scheduled)
        with st.container(border=True):
            summary_col, count_col = st.columns([3, 1])
            with summary_col:
                st.markdown("#### Today’s check-in")
                if total_count:
                    st.markdown(
                        '<span class="progress-label">Your personal progress for today</span>',
                        unsafe_allow_html=True,
                    )
                    st.progress(taken_count / total_count)
                    if taken_count == total_count:
                        st.caption("All scheduled check-ins are marked complete.")
                    elif taken_count == 0:
                        st.caption("Your check-ins will appear here as you mark doses taken.")
                    else:
                        st.caption(
                            f"{total_count - taken_count} "
                            f"{'check-in' if total_count - taken_count == 1 else 'check-ins'} "
                            "left to mark."
                        )
                else:
                    st.caption("Add a medicine to start building today’s schedule.")
            with count_col:
                st.metric("Checked in", f"{taken_count} / {total_count}")

        if not scheduled:
            st.info("Your schedule is empty. Add a medicine in My medicines.")

        for time_value, medication in scheduled:
            dose_key = f"{today_key}|{medication['id']}|{time_value}"
            already_taken = dose_key in taken_keys
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
