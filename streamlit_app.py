import os
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Oliver Forex — educational paper-analysis dashboard only.
# It does not place orders, connect to a broker, or recommend real-money trades.

PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "USD/CAD", "NZD/USD",
]
INTERVAL = "1min"
CANDLE_COUNT = 60
REFRESH_SECONDS = 60

st.set_page_config(
    page_title="Oliver Forex AI",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background: #0b1220; color: #f4f7fb; }
[data-testid="stMetric"] {
    background: #141f32; border: 1px solid #263650;
    padding: 14px; border-radius: 12px;
}
.signal-card {
    background: #141f32; border: 1px solid #263650;
    border-radius: 12px; padding: 16px; margin-bottom: 10px;
}
.small-muted { color: #9aa9bd; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Oliver Forex AI")
st.caption("متابعة تعليمية تلقائية للسوق — Paper Mode فقط")

st.warning(
    "للتعلّم والمحاكاة فقط. صعود/هبوط/انتظار هي قراءات آلية لمؤشرات فنية "
    "وليست توصيات تداول أو ضماناً للربح. لا ينفّذ التطبيق أي صفقات حقيقية."
)

api_key = st.secrets.get("TWELVE_DATA_API_KEY", os.getenv("TWELVE_DATA_API_KEY", ""))

def get_candles(pair: str):
    if not api_key:
        raise RuntimeError("أضف TWELVE_DATA_API_KEY في Streamlit Secrets أولاً.")
    params = urllib.parse.urlencode({
        "symbol": pair,
        "interval": INTERVAL,
        "outputsize": CANDLE_COUNT,
        "apikey": api_key,
        "format": "JSON",
        "timezone": "UTC",
    })
    url = "https://api.twelvedata.com/time_series?" + params
    request = urllib.request.Request(
        url, headers={"User-Agent": "OliverForexEducationalDashboard/1.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if "values" not in payload:
        message = payload.get("message") or payload.get("status") or "Unknown API response"
        raise RuntimeError(str(message))

    values = list(reversed(payload["values"]))
    frame = pd.DataFrame(values)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["close"])
    return frame

def analyze_pair(pair: str):
    candles = get_candles(pair)
    closes = candles["close"]

    # Ignore the newest candle because it may still be forming.
    closed = closes.iloc[:-1]
    if len(closed) < 22:
        raise RuntimeError("لا توجد شموع مغلقة كافية للتحليل.")

    ema9 = closed.ewm(span=9, adjust=False).mean().iloc[-1]
    ema21 = closed.ewm(span=21, adjust=False).mean().iloc[-1]

    changes = closed.diff().dropna().tail(14)
    gains = changes.clip(lower=0)
    losses = -changes.clip(upper=0)
    avg_gain = gains.mean()
    avg_loss = losses.mean()

    if avg_loss == 0:
        rsi = 100.0 if avg_gain > 0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    price = float(closed.iloc[-1])

    if ema9 > ema21 and 50 < rsi < 70:
        status = "صاعد ↑"
        tag = "BUY (محاكاة)"
        reason = f"EMA 9 أعلى من EMA 21، و RSI = {rsi:.1f}"
    elif ema9 < ema21 and 30 < rsi < 50:
        status = "هابط ↓"
        tag = "SELL (محاكاة)"
        reason = f"EMA 9 أقل من EMA 21، و RSI = {rsi:.1f}"
    else:
        status = "انتظار"
        tag = "WAIT"
        reason = f"المؤشرات لا تحقق شروط الاتجاه المحددة؛ RSI = {rsi:.1f}"

    return {
        "الزوج": pair,
        "السعر المرجعي": price,
        "الاتجاه": status,
        "الحالة": tag,
        "RSI 14": round(float(rsi), 1),
        "EMA 9": float(ema9),
        "EMA 21": float(ema21),
        "السبب": reason,
        "التحديث (UTC)": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    }

if not api_key:
    st.error("مفتاح Twelve Data غير موجود. أضفه في Streamlit → App settings → Secrets.")
    st.code('TWELVE_DATA_API_KEY = "ضع_مفتاحك_هنا"', language="toml")
    st.info("لا تضع مفتاح API داخل الكود أو في مستودع GitHub العام.")
    st.stop()

st_autorefresh(interval=REFRESH_SECONDS * 1000, key="oliver_forex_refresh")
st.caption("يفحص الأزواج تلقائياً كل 60 ثانية أثناء تشغيل التطبيق. قد تختلف حدود الطلبات حسب خطة مزوّد البيانات.")

if st.button("تحديث الآن"):
    st.rerun()

@st.cache_data(ttl=45, show_spinner=False)
def load_all_pairs():
    rows, errors = [], []
    for pair in PAIRS:
        try:
            rows.append(analyze_pair(pair))
        except Exception as exc:
            errors.append({"الزوج": pair, "الخطأ": str(exc)})
    return rows, errors

with st.spinner("يجري تحليل أزواج العملات..."):
    rows, errors = load_all_pairs()

if rows:
    df = pd.DataFrame(rows)
    up_count = sum("صاعد" in x for x in df["الاتجاه"])
    down_count = sum("هابط" in x for x in df["الاتجاه"])
    wait_count = sum(x == "انتظار" for x in df["الاتجاه"])

    c1, c2, c3 = st.columns(3)
    c1.metric("اتجاه صاعد", up_count)
    c2.metric("اتجاه هابط", down_count)
    c3.metric("انتظار", wait_count)

    st.subheader("الإشارات الحالية")
    for row in rows:
        with st.container(border=True):
            left, middle, right = st.columns([1.2, 1, 1])
            left.subheader(row["الزوج"])
            left.write(f"**{row['الاتجاه']}**")
            middle.metric("السعر المرجعي", f"{row['السعر المرجعي']:.5f}")
            right.metric("RSI 14", row["RSI 14"])
            st.write(row["السبب"])
            st.caption(f"الحالة: {row['الحالة']} · آخر تحديث: {row['التحديث (UTC)']} UTC")

    st.subheader("جدول جميع الأزواج")
    st.dataframe(
        df[["الزوج", "السعر المرجعي", "الاتجاه", "الحالة", "RSI 14", "السبب"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.error("لم تصل بيانات قابلة للتحليل. تحقق من مفتاح API وحدود الخطة.")

if errors:
    with st.expander(f"تفاصيل الأزواج التي تعذّر تحليلها ({len(errors)})"):
        st.dataframe(pd.DataFrame(errors), use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "ملاحظة: هذه النسخة تعرض قراءة المؤشرات فقط. لا تفتح صفقات، ولا تحتفظ بسجل نتائج "
    "تجريبية دائم، ولا تحسب نسبة دقة مثبتة. يجب اختبار أي طريقة على بيانات تاريخية "
    "قبل تقييمها، ولا تستخدمها لاتخاذ قرارات مالية حقيقية."
)
