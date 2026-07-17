from __future__ import annotations

from datetime import datetime

import streamlit as st
import streamlit_shadcn_ui as ui

from database import (
    delete_transaction,
    format_rupiah,
    load_logs,
    load_prices,
    parse_items,
    transaction_total,
    update_transaction,
)


def _items_preview(items: list[dict]) -> str:
    if not items:
        return "No item details available"
    return ", ".join(f"{item.get('item', 'Item')} × {item.get('quantity', 0)}" for item in items)


@st.dialog("Transaction details", width="large")
def _view_dialog(row: dict) -> None:
    items = parse_items(row["items bought"])
    total = transaction_total(items)

    cols = st.columns(3)
    with cols[0]:
        ui.card(title="Total", content=format_rupiah(total), description="Transaction value", key=f"view_total_{row['_row_id']}").render()
    with cols[1]:
        ui.card(title="Cash received", content=format_rupiah(row["cash received"]), description="Customer payment", key=f"view_cash_{row['_row_id']}").render()
    with cols[2]:
        ui.card(title="Change", content=format_rupiah(row["change"]), description="Returned amount", key=f"view_change_{row['_row_id']}").render()

    st.caption(row["date"].strftime("%d %B %Y, %I:%M %p"))
    st.divider()
    for item in items:
        name, qty, price, subtotal = st.columns([4, 1, 2, 2])
        name.write(item.get("item", ""))
        qty.write(str(item.get("quantity", 0)))
        price.write(format_rupiah(item.get("unit_price", 0)))
        subtotal.write(format_rupiah(item.get("subtotal", 0)))


@st.dialog("Edit transaction", width="large")
def _edit_dialog(row: dict) -> None:
    prices = load_prices()
    item_names = prices["item"].tolist()
    price_lookup = dict(zip(prices["item"], prices["price"]))
    original_items = parse_items(row["items bought"])

    state_key = f"edit_items_{row['_row_id']}"
    if state_key not in st.session_state:
        st.session_state[state_key] = original_items or [{"item": item_names[0], "quantity": 1}]

    date_col, time_col = st.columns(2)
    edit_date = date_col.date_input("Date", value=row["date"].date(), key=f"edit_date_{row['_row_id']}")
    edit_time = time_col.time_input("Time", value=row["date"].time(), key=f"edit_time_{row['_row_id']}")

    edited_items = []
    for index, existing in enumerate(st.session_state[state_key]):
        col_item, col_qty = st.columns([4, 1])
        default_item = existing.get("item", item_names[0])
        default_index = item_names.index(default_item) if default_item in item_names else 0
        item = col_item.selectbox("Item", item_names, index=default_index, key=f"edit_item_{row['_row_id']}_{index}")
        quantity = col_qty.number_input("Quantity", min_value=1, step=1, value=max(1, int(existing.get("quantity", 1))), key=f"edit_qty_{row['_row_id']}_{index}")
        unit_price = float(price_lookup[item])
        edited_items.append({"item": item, "quantity": int(quantity), "unit_price": round(unit_price), "subtotal": round(unit_price * int(quantity))})

    add_col, remove_col = st.columns(2)
    with add_col:
        add_clicked = ui.button(text="Add item", variant="outline", key=f"edit_add_{row['_row_id']}")
    with remove_col:
        remove_clicked = ui.button(text="Remove last item", variant="outline", key=f"edit_remove_{row['_row_id']}")
    if add_clicked:
        st.session_state[state_key].append({"item": item_names[0], "quantity": 1})
        st.rerun()
    if remove_clicked and len(st.session_state[state_key]) > 1:
        st.session_state[state_key].pop()
        st.rerun()

    total = transaction_total(edited_items)
    cash_received = st.number_input("Cash received (Rp)", min_value=0.0, value=float(row["cash received"]), step=1000.0, format="%.0f", key=f"edit_cash_{row['_row_id']}")
    change = round(max(float(cash_received) - total, 0))

    summary_cols = st.columns(2)
    with summary_cols[0]:
        ui.card(title="Updated total", content=format_rupiah(total), description="Edited transaction", key=f"edit_total_{row['_row_id']}").render()
    with summary_cols[1]:
        ui.card(title="Updated change", content=format_rupiah(change), description="Return to customer", key=f"edit_change_{row['_row_id']}").render()

    if cash_received < total:
        st.error(f"Cash is short by {format_rupiah(total - cash_received)}.")
    elif ui.button(text="Save changes", variant="default", key=f"edit_save_{row['_row_id']}"):
        update_transaction(int(row["_row_id"]), datetime.combine(edit_date, edit_time), edited_items, float(cash_received), change)
        st.session_state.pop(state_key, None)
        st.rerun()


@st.dialog("Delete transaction")
def _delete_dialog(row: dict) -> None:
    st.warning("This transaction will be permanently removed from the logs sheet.")
    st.write(f"Transaction from **{row['date'].strftime('%d %B %Y, %I:%M %p')}**")
    cancel_col, delete_col = st.columns(2)
    with cancel_col:
        cancel_clicked = ui.button(text="Cancel", variant="outline", key=f"cancel_delete_{row['_row_id']}")
    with delete_col:
        delete_clicked = ui.button(text="Delete transaction", variant="destructive", key=f"confirm_delete_{row['_row_id']}")
    if cancel_clicked:
        st.rerun()
    if delete_clicked:
        delete_transaction(int(row["_row_id"]))
        st.rerun()


def render_summary() -> None:
    st.markdown('<div class="kk-section-title">Transaction summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="kk-section-copy">Review, inspect, edit, or remove saved transactions. Newest transactions appear first.</div>', unsafe_allow_html=True)

    logs = load_logs(include_row_id=True)
    if logs.empty:
        st.info("No transactions have been saved yet.")
        return

    total_revenue = sum(transaction_total(parse_items(row["items bought"])) for _, row in logs.iterrows())
    total_change = float(logs["change"].sum())
    metric_cols = st.columns(3)
    with metric_cols[0]:
        ui.card(title="Transactions", content=str(len(logs)), description="Saved records", key="summary_count").render()
    with metric_cols[1]:
        ui.card(title="Recorded sales", content=format_rupiah(total_revenue), description="All logged transactions", key="summary_sales").render()
    with metric_cols[2]:
        ui.card(title="Change returned", content=format_rupiah(total_change), description="Across all transactions", key="summary_change").render()

    st.write("")
    with st.container(height=680, border=True):
        for _, transaction in logs.iterrows():
            row = transaction.to_dict()
            items = parse_items(row["items bought"])
            total = transaction_total(items)

            with st.container(border=True, height=205):
                info_col, action_col = st.columns([5, 1.6], vertical_alignment="center")
                with info_col:
                    st.markdown(
                        f"""
                        <div class="kk-card-title">{format_rupiah(total)}</div>
                        <div class="kk-card-meta">{row['date'].strftime('%d %B %Y, %I:%M %p')}</div>
                        <div class="kk-card-items">{_items_preview(items)}</div>
                        <div class="kk-card-stats">Cash received: {format_rupiah(row['cash received'])} &nbsp;&nbsp; Change: {format_rupiah(row['change'])}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                with action_col:
                    if ui.button(text="View details", variant="default", key=f"view_{row['_row_id']}"):
                        _view_dialog(row)
                    if ui.button(text="Edit", variant="outline", key=f"edit_{row['_row_id']}"):
                        _edit_dialog(row)
                    if ui.button(text="Delete", variant="destructive", key=f"delete_{row['_row_id']}"):
                        _delete_dialog(row)
