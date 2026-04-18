import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_reshape_tools(df: pd.DataFrame):
    st.subheader("Reshape & Transpose Tools")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    # Action Selection
    action_cols = st.columns(4)
    actions = ["Transpose"]

    # For now, only Transpose is requested, but we leave room for others (Melt, Pivot, etc.)
    for i, action in enumerate(actions):
        is_selected = st.session_state.get("reshape_action") == action
        if action_cols[i].button(action, use_container_width=True, key=f"reshape_btn_{action}", type="primary" if is_selected else "secondary"):
            st.session_state["reshape_action"] = action
            st.rerun()

    selected_action = st.session_state.get("reshape_action")
    if not selected_action:
        st.info("Select a reshaping operation above.")
        return

    st.divider()

    if selected_action == "Transpose":
        st.markdown("### 🔄 Transpose Dataset")
        st.info("Swaps rows and columns. Best for 'inverted' datasets where observations are columns.")

        c1, c2 = st.columns([1, 1])
        with c1:
            promote_headers = st.toggle("Promote first column to headers after transpose", value=True, help="If the first column contains the variable names (Name, Age, etc.), enable this to make them headers.")
        
        # PREVIEW LOGIC
        st.markdown("#### 🔍 Before vs After Preview")
        prev_cols = st.columns(2)
        
        with prev_cols[0]:
            st.caption("Current Dataset (Old)")
            st.dataframe(working_df.head(10), use_container_width=True)
            st.caption(f"Shape: {working_df.shape[0]} rows × {working_df.shape[1]} columns")

        # Calculate Transpose Preview
        try:
            if promote_headers:
                # 1. Use Col 0 as index
                # 2. Transpose
                # 3. Reset index (to get observations back as a row index or column)
                temp_df = working_df.set_index(working_df.columns[0]).T.reset_index()
                # If they want the observations names to be a column:
                temp_df.rename(columns={'index': 'Observation'}, inplace=True)
            else:
                temp_df = working_df.T.reset_index()
            
            with prev_cols[1]:
                st.caption("Transposed Dataset (New)")
                st.dataframe(temp_df.head(10), use_container_width=True)
                st.caption(f"Shape: {temp_df.shape[0]} rows × {temp_df.shape[1]} columns")

            st.divider()
            if st.button("🚀 Apply Transpose", type="primary", use_container_width=True):
                checkpoint_state()
                st.session_state["clean_df"] = temp_df
                add_log(
                    "Transpose Dataset",
                    {"promote_headers": promote_headers},
                    temp_df.columns.tolist(),
                    rows_affected={"columns_renamed": len(temp_df.columns)}
                )
                st.success("Dataset successfully transposed!")
                st.session_state["reshape_action"] = None # Reset action on success
                st.rerun()

        except Exception as e:
            st.error(f"⚠️ Could not transpose dataset: {e}")
            st.info("Common issues: Duplicate values in the first column when 'Promote Headers' is ON.")
