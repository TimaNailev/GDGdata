import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_duplicates_cleaning(df: pd.DataFrame):
    st.subheader("Duplicate Handling")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    # DETECTION MODE
    st.markdown("### Detection Mode")
    mode_cols = st.columns(2)
    modes = ["Full row", "Subset"]

    for i, mode in enumerate(modes):
        is_selected = st.session_state.get("dup_mode") == mode
        if mode_cols[i].button(mode, use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state["dup_mode"] = mode
            st.session_state["dup_subset_cols"] = []
            st.rerun()

    selected_mode = st.session_state.get("dup_mode")

    # SUBSET COLUMN SELECTOR
    subset_cols = None
    if selected_mode == "Subset":
        subset_cols = st.multiselect(
            "Select columns for duplicate detection",
            working_df.columns, key="dup_subset_cols"
        )

    # DETECT DUPLICATES
    if selected_mode == "Full row":
        dup_mask = working_df.duplicated(keep=False)
    elif selected_mode == "Subset":
        if not subset_cols:
            st.warning("Please select at least one column.")
            return
        dup_mask = working_df.duplicated(subset=subset_cols, keep=False)
    else:
        st.info("Select detection mode to continue.")
        return

    duplicate_df = working_df[dup_mask]
    st.markdown(f"**Found {len(duplicate_df)} duplicate rows**")
    st.divider()

    # ACTION BUTTONS
    st.markdown("### Actions")
    action_cols = st.columns(2)
    actions = ["Keep first", "Keep last"]

    for i, action in enumerate(actions):
        is_selected = st.session_state.get("dup_action") == action
        if action_cols[i].button(action, use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state["dup_action"] = action
            st.rerun()

    selected_action = st.session_state.get("dup_action")

    # APPLY ACTION
    if dup_mask is None or len(duplicate_df) == 0:
        st.info("No duplicates to process.")
        return

    if selected_action:
        if st.button("Apply duplicate cleaning"):
            checkpoint_state()
            if selected_mode == "Full row":
                subset = None
            else:
                subset = subset_cols
            keep = "first" if selected_action == "Keep first" else "last"
            cleaned = working_df.drop_duplicates(subset=subset, keep=keep)
            rows_removed = len(working_df) - len(cleaned)
            st.session_state["clean_df"] = cleaned
            add_log(f"Remove Duplicates ({selected_mode})", {"keep": keep, "mode": selected_mode}, list(working_df.columns) if selected_mode == "Full row" else subset, rows_affected={"rows_deleted": rows_removed})
            st.success("Duplicates removed successfully")

    st.divider()

    # SHOW DUPLICATE GROUPS
    st.markdown("### Duplicate Groups")

    if len(duplicate_df) > 0:
        if selected_mode == "Full row":
            group_cols = list(working_df.columns)
        elif selected_mode == "Subset":
            if not subset_cols or len(subset_cols) == 0:
                st.warning("Please select columns to group duplicates.")
                return
            group_cols = list(subset_cols)
        else:
            st.warning("Invalid mode.")
            return

        if group_cols is None or len(group_cols) == 0:
            st.error("Grouping failed: no valid columns.")
            return
        grouped = duplicate_df.copy()
        grouped["_group_id"] = grouped.groupby(group_cols).ngroup()
        grouped = grouped.sort_values("_group_id")
        st.dataframe(grouped, use_container_width=True)
    else:
        st.info("No duplicates found.")
