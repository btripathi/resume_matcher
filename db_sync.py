import os
import time
import streamlit as st


def ensure_db_synced_on_startup(github_sync):
    if "db_synced" in st.session_state:
        return
    with st.spinner("🔄 Checking GitHub for Database..."):
        if github_sync.pull_db():
            st.toast("✅ Database Restored from GitHub!", icon="☁️")
        else:
            st.toast("ℹ️ No remote DB found. Using Local.", icon="💻")
    st.session_state.db_synced = True


def init_write_mode_state(local_lm_available, github_sync):
    env_read_only = os.getenv("RESUME_MATCHER_READ_ONLY", "").lower() in ("1", "true", "yes")
    env_write = os.getenv("RESUME_MATCHER_WRITE_MODE", "").lower() in ("1", "true", "yes")
    if env_write:
        st.session_state.write_mode = True
        st.session_state.write_mode_warned = False
        st.session_state.write_mode_locked = False
    elif env_read_only:
        st.session_state.write_mode = False
        st.session_state.write_mode_locked = True

    # Auto-enable write mode locally if configured
    try:
        auto_write = st.secrets.get("writer", {}).get("auto_write_mode", False)
        writer_name_auto = st.secrets.get("writer", {}).get("name", "")
        if not st.session_state.write_mode_locked and auto_write and local_lm_available and not st.session_state.write_mode:
            lock_timeout = st.secrets.get("writer", {}).get("lock_timeout_hours", 6)
            lock_info = github_sync.get_lock(timeout_hours=lock_timeout)
            if lock_info and isinstance(lock_info, dict) and lock_info.get("owner") == (writer_name_auto or "unknown"):
                st.session_state.write_mode = True
            else:
                ok, _ = github_sync.acquire_lock(writer_name_auto or "unknown", timeout_hours=lock_timeout)
                if ok:
                    st.session_state.write_mode = True
    except Exception:
        pass


def sync_db_if_allowed(github_sync):
    if st.session_state.write_mode:
        return github_sync.push_db()
    if not st.session_state.write_mode_warned:
        st.warning("Read-only mode: changes are not synced to shared DB. Enable Write Mode to push.")
        st.session_state.write_mode_warned = True
    return False


def render_write_mode_controls(github_sync):
    st.divider()
    st.write("### Write Mode")
    lock_timeout = 6
    try:
        lock_timeout = st.secrets.get("writer", {}).get("lock_timeout_hours", 6)
    except Exception:
        lock_timeout = 6

    lock_info = github_sync.get_lock(timeout_hours=lock_timeout)
    if lock_info and isinstance(lock_info, dict):
        owner = lock_info.get("owner", "unknown")
        created = lock_info.get("created_at", "unknown time")
        if lock_info.get("expired"):
            st.caption(f"Write lock: **{owner}** since {created} (expired)")
        else:
            st.caption(f"Write lock: **{owner}** since {created}")
    else:
        st.caption("Write lock: none")

    writer_name_default = ""
    try:
        writer_name_default = st.secrets.get("writer", {}).get("name", "")
    except Exception:
        writer_name_default = ""
    writer_name = st.text_input("Writer name", value=writer_name_default, key="writer_name")
    writer_password = st.text_input("Write password", type="password", key="writer_password")

    st.caption(f"Lock auto-expires after {lock_timeout} hours. Use Release before closing if possible.")

    if st.session_state.write_mode_locked:
        st.info("Write mode is locked by the launcher. Re-run with write mode enabled to allow shared DB updates.")

    if st.button("Enable Write Mode", disabled=st.session_state.write_mode_locked):
        expected = None
        try:
            expected = st.secrets.get("writer", {}).get("password")
        except Exception:
            expected = None
        if not expected:
            st.error("Write password not configured in secrets.")
        elif writer_password != expected:
            st.error("Incorrect write password.")
        else:
            if lock_info and isinstance(lock_info, dict) and lock_info.get("owner") == (writer_name or "unknown"):
                st.session_state.write_mode = True
                st.session_state.write_mode_warned = False
                st.success("Write mode resumed (existing lock).")
                time.sleep(0.2)
                st.rerun()
            else:
                ok, msg = github_sync.acquire_lock(writer_name or "unknown", timeout_hours=lock_timeout)
                if ok:
                    st.session_state.write_mode = True
                    st.session_state.write_mode_warned = False
                    st.success(msg)
                    time.sleep(0.2)
                    st.rerun()
                else:
                    st.error(msg)

    if st.session_state.write_mode and not st.session_state.write_mode_locked:
        if st.button("Disable Write Mode / Release Lock"):
            ok, msg = github_sync.release_lock(writer_name or "unknown")
            if ok:
                st.session_state.write_mode = False
                st.session_state.write_mode_warned = False
                st.success(msg)
                time.sleep(0.2)
                st.rerun()
            else:
                st.error(msg)

    if st.button("Force Unlock (Admin)"):
        expected = None
        try:
            expected = st.secrets.get("writer", {}).get("password")
        except Exception:
            expected = None
        if not expected:
            st.error("Write password not configured in secrets.")
        elif writer_password != expected:
            st.error("Incorrect write password.")
        else:
            ok, msg = github_sync.release_lock(writer_name or "unknown", force=True)
            if ok:
                st.session_state.write_mode = False
                st.session_state.write_mode_warned = False
                st.success(msg)
                time.sleep(0.2)
                st.rerun()
            else:
                st.error(msg)
