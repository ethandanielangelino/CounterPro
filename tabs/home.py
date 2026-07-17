from __future__ import annotations

import streamlit as st
import streamlit_shadcn_ui as ui

from database import format_rupiah, load_prices, save_transaction


def _reset_sale() -> None:
    st.session_state.sale_row_count = 1
    st.session_state.sale_result = None
    st.session_state.sale_version = st.session_state.get("sale_version", 0) + 1


def render_home() -> None:
    prices = load_prices()

    st.session_state.setdefault("sale_row_count", 1)
    st.session_state.setdefault("sale_result", None)
    st.session_state.setdefault("sale_version", 0)

    st.markdown('<div class="kk-section-title">New transaction</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kk-section-copy">Select the items purchased, enter quantities, and calculate the customer’s change.</div>',
        unsafe_allow_html=True,
    )

    if prices.empty:
        st.warning("The prices sheet is empty. Add items and prices to database.xlsx, then refresh this page.")
        return

    item_names = prices["item"].tolist()
    price_lookup = dict(zip(prices["item"], prices["price"]))
    version = st.session_state.sale_version

    with st.container(border=True):
        ui.badges(
            badge_list=[("ITEMS PURCHASED", "secondary")],
            class_name="flex gap-2",
            key=f"items_badge_{version}",
        )
        st.write("")
        selected_rows = []

        for row_index in range(st.session_state.sale_row_count):
            col_item, col_qty, col_price, col_remove = st.columns([5, 1.6, 2, 1.3], vertical_alignment="bottom")
            selected_item = col_item.selectbox(
                "Item",
                item_names,
                key=f"sale_item_{version}_{row_index}",
            )
            quantity = col_qty.number_input(
                "Quantity",
                min_value=1,
                step=1,
                value=1,
                key=f"sale_qty_{version}_{row_index}",
            )
            unit_price = float(price_lookup[selected_item])

            with col_price:
                ui.card(
                    title="Unit price",
                    content=format_rupiah(unit_price),
                    description="Per item",
                    key=f"unit_price_card_{version}_{row_index}",
                ).render()

            with col_remove:
                remove_clicked = ui.button(
                    text="Remove",
                    variant="outline",
                    key=f"sale_remove_{version}_{row_index}",
                )
            if remove_clicked and st.session_state.sale_row_count > 1:
                st.session_state.sale_row_count -= 1
                st.session_state.sale_result = None
                st.rerun()

            selected_rows.append(
                {
                    "item": selected_item,
                    "quantity": int(quantity),
                    "unit_price": round(unit_price),
                    "subtotal": round(unit_price * int(quantity)),
                }
            )
            if row_index < st.session_state.sale_row_count - 1:
                st.divider()

        st.write("")
        if ui.button(text="Add another item", variant="outline", key=f"add_item_{version}"):
            st.session_state.sale_row_count += 1
            st.session_state.sale_result = None
            st.rerun()

    st.write("")
    cash_received = st.number_input(
        "Cash received (Rp)",
        min_value=0.0,
        step=1000.0,
        format="%.0f",
        key=f"sale_cash_{version}",
        help="Enter the amount handed over by the customer.",
    )

    if ui.button(text="Calculate transaction", variant="default", key=f"calculate_{version}"):
        total = round(sum(row["subtotal"] for row in selected_rows))
        change = round(max(float(cash_received) - total, 0))
        balance_due = round(max(total - float(cash_received), 0))
        st.session_state.sale_result = {
            "items": selected_rows,
            "total": total,
            "cash_received": float(cash_received),
            "change": change,
            "balance_due": balance_due,
        }

    result = st.session_state.sale_result
    if result:
        st.write("")
        total_col, cash_col, change_col = st.columns(3)
        with total_col:
            ui.card(title="Total", content=format_rupiah(result["total"]), description="Transaction value", key=f"total_{version}").render()
        with cash_col:
            ui.card(title="Cash received", content=format_rupiah(result["cash_received"]), description="Customer payment", key=f"cash_{version}").render()
        with change_col:
            ui.card(title="Change", content=format_rupiah(result["change"]), description="Return to customer", key=f"change_{version}").render()

        st.write("")
        with st.container(border=True):
            ui.badges(badge_list=[("TRANSACTION DETAILS", "secondary")], class_name="flex gap-2", key=f"result_badge_{version}")
            st.write("")
            for item in result["items"]:
                left, right = st.columns([5, 2])
                left.markdown(f"<div class='kk-item-line'><strong>{item['item']}</strong><br><span style='color:#64748b'>Quantity: {item['quantity']}</span></div>", unsafe_allow_html=True)
                right.markdown(f"<div class='kk-item-line' style='text-align:right'><strong>{format_rupiah(item['subtotal'])}</strong></div>", unsafe_allow_html=True)

        if result["balance_due"] > 0:
            st.error(f"Insufficient cash. Remaining amount: {format_rupiah(result['balance_due'])}")
        elif ui.button(text="Save transaction", variant="default", key=f"save_{version}"):
            save_transaction(result["items"], result["cash_received"], result["change"])
            _reset_sale()
            st.toast("Transaction saved to database.xlsx.")
            st.rerun()
