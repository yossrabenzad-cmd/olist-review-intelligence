"""RFM toolkit: customer segmentation and action plans for any webshop.

Works on any order table that has a customer ID, an order ID, an order date
and an order amount. Market-specific actions live in PLAYBOOKS, so the same
segmentation can be turned into a plan for different markets.

Built and tested on the Olist Brazilian e-commerce dataset (93,356 customers).
"""
import pandas as pd


def build_rfm(orders_df, customer_col, date_col, amount_col, order_col, ref_date=None):
    """One row per customer with recency (days), frequency (orders) and monetary (total spend)."""
    if ref_date is None:
        ref_date = orders_df[date_col].max() + pd.Timedelta(days=1)

    out = orders_df.groupby(customer_col).agg(
        last_order=(date_col, 'max'),
        frequency=(order_col, 'nunique'),
        monetary=(amount_col, 'sum'),
    )
    out['recency'] = (ref_date - out['last_order']).dt.days
    return out


def score_rfm(rfm_df, n_groups=5, freq_bins=(0, 1, 2, float('inf'))):
    """Adds R, M (1 = worst, n_groups = best) and F (1 to len(freq_bins) - 1) scores."""
    out = rfm_df.copy()
    labels_up = list(range(1, n_groups + 1))

    out['R'] = pd.qcut(out['recency'].rank(method='first'), q=n_groups, labels=labels_up[::-1]).astype(int)
    out['M'] = pd.qcut(out['monetary'].rank(method='first'), q=n_groups, labels=labels_up).astype(int)

    f_labels = list(range(1, len(freq_bins)))
    out['F'] = pd.cut(out['frequency'], bins=list(freq_bins), labels=f_labels).astype(int)
    return out


def assign_segments(scored_df, recent_min=4, value_min=4, repeat_min=2, lost_max=1):
    """Adds a 'segment' column using adjustable R, F, M cut-offs."""
    def rule(row):
        if row['F'] >= repeat_min and row['R'] >= recent_min:
            return 'Champions'
        if row['F'] >= repeat_min:
            return 'Loyal, slipping'
        if row['R'] >= recent_min and row['M'] >= value_min:
            return 'New, high value'
        if row['R'] >= recent_min:
            return 'New'
        if row['R'] > lost_max and row['M'] >= value_min:
            return 'At risk, high value'
        if row['R'] > lost_max:
            return 'Hibernating'
        return 'Lost'

    out = scored_df.copy()
    out['segment'] = out.apply(rule, axis=1)
    return out


def profile_segments(segmented_df):
    """Size, value and recency per segment, sorted by revenue share."""
    p = segmented_df.groupby('segment').agg(
        customers=('segment', 'count'),
        revenue=('monetary', 'sum'),
        median_spend=('monetary', 'median'),
        median_recency=('recency', 'median'),
    )
    p['customer_share'] = p['customers'] / p['customers'].sum() * 100
    p['revenue_share'] = p['revenue'] / p['revenue'].sum() * 100
    return p.sort_values('revenue_share', ascending=False).round(1)


# Marketing decisions per segment, the same in every market.
BASE_PLAN = {
    'New, high value':     {'priority': 1, 'effort': 'Personal',      'step_1': 'Thank-you, care tips, cross-sell from their category', 'step_2': 'After 14 days with no order: free shipping'},
    'At risk, high value': {'priority': 1, 'effort': 'Personal',      'step_1': 'Check last experience; apology first if it was bad, then new arrivals in their category', 'step_2': 'After 14 days: 10% win-back offer'},
    'Champions':           {'priority': 2, 'effort': 'Personal',      'step_1': 'Early access and VIP perks, ask for a review', 'step_2': 'Loyalty reward on next order'},
    'Loyal, slipping':     {'priority': 2, 'effort': 'Semi-personal', 'step_1': '"We miss you" with cross-sell', 'step_2': 'After 14 days: free shipping'},
    'New':                 {'priority': 3, 'effort': 'Automated',     'step_1': 'Welcome series', 'step_2': 'Small incentive for order two'},
    'Hibernating':         {'priority': 3, 'effort': 'Automated',     'step_1': 'Seasonal reminders (Black Friday)', 'step_2': 'None'},
    'Lost':                {'priority': 4, 'effort': 'Automated',     'step_1': 'Big seasonal campaigns only', 'step_2': 'None'},
}

# What changes per market: channels, retargeting and local notes.
PLAYBOOKS = {
    'brazil': {
        'channels': {'Personal': 'Email + WhatsApp', 'Semi-personal': 'Email + WhatsApp', 'Automated': 'Email'},
        'retargeting': 'Meta (Facebook, Instagram)',
        'note': 'Offer boleto and installments on higher-priced items.',
    },
    'denmark': {
        'channels': {'Personal': 'Email + SMS', 'Semi-personal': 'Email', 'Automated': 'Email'},
        'retargeting': 'Meta (Facebook, Instagram)',
        'note': 'MobilePay at checkout; marketing email and SMS need consent; Trustpilot reviews are highly visible.',
    },
}


def build_action_plan(segmented_df, market, control_share=0.10):
    """Segment profile plus actions and channels for one market."""
    book = PLAYBOOKS[market]
    plan = profile_segments(segmented_df)

    plan['priority'] = plan.index.map(lambda s: BASE_PLAN[s]['priority'])
    plan['effort'] = plan.index.map(lambda s: BASE_PLAN[s]['effort'])
    plan['channel'] = plan['effort'].map(book['channels'])
    plan['step_1'] = plan.index.map(lambda s: BASE_PLAN[s]['step_1'])
    plan['step_2'] = plan.index.map(lambda s: BASE_PLAN[s]['step_2'])
    plan['control_group'] = (plan['customers'] * control_share).round().astype(int)

    print(f"Market: {market} | Retargeting: {book['retargeting']} | {book['note']}")
    return plan.sort_values(['priority', 'revenue_share'], ascending=[True, False])


def run_rfm(orders_df, customer_col, date_col, amount_col, order_col, market,
            ref_date=None, n_groups=5, freq_bins=(0, 1, 2, float('inf')),
            recent_min=4, value_min=4, control_share=0.10):
    """Whole pipeline in one call. Returns (customers with segments, action plan)."""
    rfm = build_rfm(orders_df, customer_col, date_col, amount_col, order_col, ref_date)
    rfm = score_rfm(rfm, n_groups=n_groups, freq_bins=freq_bins)
    rfm = assign_segments(rfm, recent_min=recent_min, value_min=value_min)
    plan = build_action_plan(rfm, market, control_share=control_share)
    return rfm, plan
