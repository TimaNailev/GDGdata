import pandas as pd
import streamlit as st
from logger import add_log, checkpoint_state


def show_categorical_tools(df: pd.DataFrame):
    st.subheader("Categorical Data Toolkit")

    if st.session_state.get("clean_df") is None:
        st.session_state["clean_df"] = df.copy()

    working_df = st.session_state["clean_df"]

    from utils import get_columns_by_type
    cat_cols = get_columns_by_type(working_df, "categorical")

    if not cat_cols:
        st.info("No categorical (text) columns found in your dataset.")
        return

    selected_col = st.selectbox("Select categorical column", cat_cols, key="cat_column")

    if not selected_col:
        st.info("Please select a column to continue.")
        return

    series = working_df[selected_col]

    stat_cols = st.columns(4)
    stat_cols[0].metric("Unique Values", int(series.nunique()))
    stat_cols[1].metric("Missing", int(series.isna().sum()))
    stat_cols[2].metric("Most Frequent", str(series.mode().iloc[0]) if not series.mode().empty else "N/A")
    stat_cols[3].metric("Total Rows", len(series))
    st.divider()

    # ACTION BUTTONS
    st.markdown("### Tools")
    action_cols = st.columns(4)
    actions = ["Standardize", "Mapping", "Rare Grouping", "One-Hot Encoding"]

    for i, action_name in enumerate(actions):
        is_selected = st.session_state.get("cat_action") == action_name
        if action_cols[i].button(action_name, use_container_width=True, key=f"cat_action_{i}", type="primary" if is_selected else "secondary"):
            st.session_state["cat_action"] = action_name
            st.rerun()

    selected_action = st.session_state.get("cat_action")

    if not selected_action:
        st.info("Select a tool above to get started.")
        return

    st.divider()

    # 1. STANDARDIZE
    if selected_action == "Standardize":
        st.markdown("### Standardize Text Values")
        st.caption("Clean up inconsistent text by trimming whitespace, changing case, etc.")
        trim_ws = st.checkbox("Trim whitespace", value=True, key="cat_std_trim")
        lowercase = st.checkbox("Convert to lowercase", key="cat_std_lower")
        titlecase = st.checkbox("Convert to Title Case", key="cat_std_title")

        preview = series.copy()
        if trim_ws:
            preview = preview.str.strip()
        if lowercase:
            preview = preview.str.lower()
        if titlecase:
            preview = preview.str.title()

        st.markdown("**Preview**")
        prev_cols = st.columns(2)
        with prev_cols[0]:
            st.markdown("*Original*")
            st.dataframe(pd.DataFrame({"Original": series.head(10).values}), use_container_width=True, hide_index=True)
        with prev_cols[1]:
            st.markdown("*After Standardization*")
            st.dataframe(pd.DataFrame({"Standardized": preview.head(10).values}), use_container_width=True, hide_index=True)

        changed_count = int((series.fillna("") != preview.fillna("")).sum())
        st.caption(f"{changed_count} value(s) will be modified.")

        if st.button("Apply Standardization", key="apply_cat_std"):
            checkpoint_state()
            result = working_df[selected_col].copy()
            if trim_ws:
                result = result.str.strip()
            if lowercase:
                result = result.str.lower()
            if titlecase:
                result = result.str.title()
            rows_changed = int((working_df[selected_col].fillna('') != result.fillna('')).sum())
            working_df[selected_col] = result
            st.session_state["clean_df"] = working_df
            add_log("Standardize Text", {"trim": trim_ws, "lower": lowercase, "title": titlecase}, [selected_col], rows_affected={"rows_modified": rows_changed})
            st.success("Standardization applied successfully.")
            st.rerun()

    # 2. MAPPING / REPLACEMENT
    elif selected_action == "Mapping":
        st.markdown("### Value Mapping / Replacement")
        st.caption("Rename or merge category values manually or use AI to find canonical versions.")
        
        from ai_assistant import get_canonical_mapping
        import json
        import re

        # --- AI SUGGESTION ENGINE ---
        if st.button("🎖️ AI Suggest Canonical Mapping", use_container_width=True, type="secondary"):
            with st.spinner("Captain Price is analyzing text variants..."):
                counts = series.value_counts().to_dict()
                response = get_canonical_mapping(selected_col, counts)
                
                # Parse JSON
                json_match = re.search(r"```json\s*\n?(.*?)\n?```", response, re.DOTALL)
                if json_match:
                    try:
                        suggestions = json.loads(json_match.group(1).strip())
                        st.session_state["cat_ai_suggestions"] = suggestions
                    except:
                        st.error("Failed to parse AI response. Try again.")
                else:
                    # If it's a known error message (like "Offline"), show it directly
                    if "Captain Price is offline" in response or "⚠️" in response:
                        st.markdown(response)
                    else:
                        st.error("AI returned an invalid format. Ensure AI is online.")
                        st.caption(f"Raw Response: {response[:200]}...")
        
        ai_sugg = st.session_state.get("cat_ai_suggestions")
        
        if ai_sugg:
            with st.expander("🎖️ Captain Price's Suggestions", expanded=True):
                sugg_list = ai_sugg.get("mappings", [])
                s_df = pd.DataFrame(sugg_list)
                if not s_df.empty:
                    st.markdown("**Review Suggested Standardizations:**")
                    # Editable suggestion table
                    edited_sugg = st.data_editor(s_df, use_container_width=True, hide_index=True, key="ai_sugg_editor")
                    
                    unmapped = ai_sugg.get("unmapped", [])
                    if unmapped:
                        st.caption(f"ℹ️ Unmapped/Ambiguous values: {', '.join(unmapped)}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Discard Suggestions", use_container_width=True):
                        del st.session_state["cat_ai_suggestions"]
                        st.rerun()
                        
                    if c2.button("Apply Suggested Mapping", type="primary", use_container_width=True):
                        checkpoint_state()
                        # Build mapping dict from edited suggestions
                        # Rule: Only apply if confidence is High OR if user kept it in the editor
                        final_map = {row["raw"]: row["canonical"] for _, row in edited_sugg.iterrows() if row["canonical"]}
                        
                        new_col = f"{selected_col}_canonical"
                        working_df[new_col] = working_df[selected_col].replace(final_map)
                        
                        st.session_state["clean_df"] = working_df
                        add_log("AI Canonical Mapping", {"mapping": final_map, "source": selected_col}, [new_col], rows_affected={"rows_modified": len(working_df)})
                        st.success(f"Mission accomplished. Created new column: **{new_col}**")
                        del st.session_state["cat_ai_suggestions"]
                        st.rerun()
                else:
                    st.info("Captain Price couldn't find any obvious variants to merge.")

        st.divider()
        st.markdown("#### Manual Mapping")
        unique_vals = series.dropna().unique().tolist()
        unique_vals.sort(key=str)

        mapping_df = pd.DataFrame({"Old Value": unique_vals, "New Value": [""] * len(unique_vals)})
        edited_map = st.data_editor(mapping_df, use_container_width=True, hide_index=True, num_rows="fixed", key="cat_map_editor")
        replace_unmatched = st.checkbox("Replace unmatched values with 'Other'", key="cat_map_other")

        mapping_dict = {}
        for _, row in edited_map.iterrows():
            old_val = row["Old Value"]
            new_val = row["New Value"]
            if new_val and str(new_val).strip() != "":
                mapping_dict[old_val] = str(new_val).strip()

        if mapping_dict:
            st.markdown("**Preview (Manual)**")
            preview = series.replace(mapping_dict)
            if replace_unmatched:
                mapped_new_vals = set(mapping_dict.values())
                preview = preview.apply(lambda x: x if pd.isna(x) or x in mapped_new_vals else "Other")
            prev_cols = st.columns(2)
            with prev_cols[0]:
                st.markdown("*Original*")
                st.dataframe(pd.DataFrame({"Original": series.head(10).values}), use_container_width=True, hide_index=True)
            with prev_cols[1]:
                st.markdown("*After Mapping*")
                st.dataframe(pd.DataFrame({"Mapped": preview.head(10).values}), use_container_width=True, hide_index=True)
            changed_count = int((series.fillna("") != preview.fillna("")).sum())
            st.caption(f"{changed_count} value(s) will be modified.")

        if st.button("Apply Manual Mapping", key="apply_cat_map"):
            checkpoint_state()
            if not mapping_dict:
                st.warning("Please fill in at least one 'New Value' to apply.")
            else:
                rows_changed = int((working_df[selected_col] != working_df[selected_col].replace(mapping_dict)).sum())
                if replace_unmatched:
                    mapped_new_vals = set(mapping_dict.values())
                    working_df[selected_col] = working_df[selected_col].apply(
                        lambda x: x if pd.isna(x) or x in mapped_new_vals else "Other"
                    )
                st.session_state["clean_df"] = working_df
                add_log("Value Mapping", {"mapping": mapping_dict, "replace_unmatched": replace_unmatched}, [selected_col], rows_affected={"rows_modified": rows_changed})
                st.success("Manual mapping applied successfully.")
                st.rerun()

    # 3. RARE CATEGORY GROUPING
    elif selected_action == "Rare Grouping":
        st.markdown("### Rare Category Grouping")
        st.caption("Merge infrequent categories into a single 'Other' group to reduce noise.")
        method_cols = st.columns(2)
        with method_cols[0]:
            threshold_pct = st.slider("Threshold (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.5, key="cat_rare_pct")
        with method_cols[1]:
            min_count = st.number_input("OR minimum count", min_value=0, value=0, step=1, key="cat_rare_count", help="Set to 0 to use percentage threshold instead.")

        value_counts = series.value_counts()
        total = len(series.dropna())

        if min_count > 0:
            rare_cats = value_counts[value_counts < min_count].index.tolist()
            method_label = f"count < {min_count}"
        else:
            rare_cats = value_counts[(value_counts / total * 100) < threshold_pct].index.tolist()
            method_label = f"< {threshold_pct}%"

        st.markdown(f"**{len(rare_cats)} rare categor{'y' if len(rare_cats) == 1 else 'ies'} detected** ({method_label})")

        if rare_cats:
            rare_info = value_counts[value_counts.index.isin(rare_cats)]
            rare_df = pd.DataFrame({"Category": rare_info.index, "Count": rare_info.values, "%": (rare_info.values / total * 100).round(2)})
            st.dataframe(rare_df, use_container_width=True, hide_index=True)

            st.markdown("**Preview**")
            preview = series.copy()
            preview = preview.apply(lambda x: "Other" if x in rare_cats else x)
            prev_cols = st.columns(2)
            with prev_cols[0]:
                st.markdown("*Original value counts*")
                orig_vc = series.value_counts().reset_index()
                orig_vc.columns = ["Category", "Count"]
                st.dataframe(orig_vc.head(15), use_container_width=True, hide_index=True)
            with prev_cols[1]:
                st.markdown("*After grouping*")
                new_vc = preview.value_counts().reset_index()
                new_vc.columns = ["Category", "Count"]
                st.dataframe(new_vc.head(15), use_container_width=True, hide_index=True)

            if st.button("Apply Rare Grouping", key="apply_cat_rare"):
                checkpoint_state()
                working_df[selected_col] = working_df[selected_col].apply(lambda x: "Other" if x in rare_cats else x)
                st.session_state["clean_df"] = working_df
                add_log("Rare Grouping", {"threshold_pct": threshold_pct, "min_count": min_count, "rare_categories": rare_cats}, [selected_col], rows_affected={"rows_modified": len(working_df[working_df[selected_col] == "Other"])})
                st.success(f"Grouped {len(rare_cats)} rare categories into 'Other'.")
                st.rerun()
        else:
            st.success("No rare categories found with the current threshold.")

    # 4. ONE-HOT ENCODING
    elif selected_action == "One-Hot Encoding":
        st.markdown("### One-Hot Encoding")
        st.caption(f"Creates a new binary column for each unique value in **{selected_col}**, then removes the original column.")
        unique_count = int(series.nunique())

        if unique_count > 50:
            st.warning(f"⚠️ **{selected_col}** has {unique_count} unique values. Consider grouping rare categories first.")
        elif unique_count > 15:
            st.info(f"This will create {unique_count} new binary columns.")

        st.markdown("**Preview — new columns**")
        preview_dummies = pd.get_dummies(series.head(10), prefix=selected_col).astype(int)
        st.dataframe(preview_dummies, use_container_width=True, hide_index=True)
        st.caption(f"New columns: {', '.join(preview_dummies.columns.tolist())}")

        if st.button("Apply One-Hot Encoding", key="apply_cat_onehot"):
            checkpoint_state()
            dummies = pd.get_dummies(working_df[selected_col], prefix=selected_col).astype(int)
            working_df = pd.concat([working_df.drop(columns=[selected_col]), dummies], axis=1)
            st.session_state["clean_df"] = working_df
            add_log("One-Hot Encoding", {"num_columns": len(dummies.columns)}, [selected_col], rows_affected={"columns_created": len(dummies.columns)})
            st.success(f"One-hot encoded '{selected_col}' → {len(dummies.columns)} new columns created.")
            st.rerun()
